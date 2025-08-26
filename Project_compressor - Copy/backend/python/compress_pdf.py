#!/usr/bin/env python3
import sys
import os
import io
import math
import shutil
import uuid
import fitz  # PyMuPDF
from PIL import Image

# -------------------------
# Helpers
# -------------------------
def bytes_from_jpeg_image(img, quality):
    buf = io.BytesIO()
    img.save(buf, format="JPEG", optimize=True, quality=int(quality))
    return buf.getvalue()

def try_quality_search(img, target_bytes, max_q=95, min_q=5):
    """Binary search for highest quality <= target_bytes."""
    low, high = min_q, max_q
    best = None
    while low <= high:
        mid = (low + high) // 2
        data = bytes_from_jpeg_image(img, mid)
        size = len(data)
        if size <= target_bytes:
            best = data
            low = mid + 1
        else:
            high = mid - 1
    return best

def write_exact(path, data, exact_size):
    """Write file and pad with null bytes up to exact_size."""
    with open(path, "wb") as f:
        f.write(data)
    cur = os.path.getsize(path)
    if cur < exact_size:
        pad = exact_size - cur
        with open(path, "ab") as f:
            f.write(b"\x00" * pad)

def safe_remove(path):
    try:
        if os.path.isfile(path):
            os.remove(path)
        elif os.path.isdir(path):
            shutil.rmtree(path)
    except Exception:
        pass

# -------------------------
# Args & setup
# -------------------------
if len(sys.argv) < 3:
    print("Usage: python compress_pdf.py <input_pdf> <target_kb>")
    sys.exit(1)

input_pdf = sys.argv[1]
try:
    target_kb = float(sys.argv[2])
except Exception:
    print("ERROR: target_kb must be a number")
    sys.exit(1)

target_bytes = int(round(target_kb * 1024))

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUTPUT_DIR = os.path.join(BASE_DIR, "uploads", "compressed")
os.makedirs(OUTPUT_DIR, exist_ok=True)

if not os.path.exists(input_pdf):
    print(f"ERROR: input file does not exist: {input_pdf}")
    sys.exit(1)

name_only = os.path.splitext(os.path.basename(input_pdf))[0]
out_pdf = os.path.join(OUTPUT_DIR, f"{name_only}.pdf")

orig_bytes = os.path.getsize(input_pdf)
orig_kb = orig_bytes / 1024.0

# -------------------------
# Quick path
# -------------------------
if target_bytes >= orig_bytes:
    try:
        shutil.copy(input_pdf, out_pdf)
        write_exact(out_pdf, open(out_pdf, "rb").read(), target_bytes)
        final_kb = os.path.getsize(out_pdf) / 1024.0
        print(f"Original: {orig_kb:.2f} KB | Target: {target_kb:.2f} KB | Final: {final_kb:.2f} KB (copied/padded)")
        print(f"FINAL_OUTPUT_PATH::{out_pdf}")
        sys.exit(0)
    except Exception as e:
        print(f"ERROR: Could not copy/pad original PDF: {e}")
        sys.exit(1)

# -------------------------
# Main compression
# -------------------------
temp_id = uuid.uuid4().hex[:8]
temp_dir = os.path.join(BASE_DIR, "temp_pdf_images_" + temp_id)
os.makedirs(temp_dir, exist_ok=True)

try:
    doc = fitz.open(input_pdf)
    page_count = len(doc)
    rendered_paths, page_areas, page_sizes = [], [], []

    for i, page in enumerate(doc):
        rect = page.rect
        pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0), alpha=False)
        img_path = os.path.join(temp_dir, f"page_{i+1}.jpg")
        pix.save(img_path)
        with Image.open(img_path) as im:
            page_sizes.append(im.size)
            page_areas.append(im.size[0] * im.size[1])
        rendered_paths.append(img_path)
    doc.close()

    total_area = sum(page_areas)
    overhead_estimate = 2048 * page_count
    image_budget = max(1, target_bytes - overhead_estimate)
    if image_budget <= 0:
        raise Exception("Target too small for PDF overhead; choose larger target")

    scale = 1.0
    min_side = 64
    compressed_image_data_list = None

    while True:
        per_page_targets = [max(512, int(image_budget * (a / total_area))) for a in page_areas]
        temp_data_list = []

        for idx, src_img in enumerate(rendered_paths):
            with Image.open(src_img) as im0:
                new_w = max(min_side, int(page_sizes[idx][0] * scale))
                new_h = max(min_side, int(page_sizes[idx][1] * scale))
                im = im0.resize((new_w, new_h), Image.LANCZOS) if (new_w, new_h) != page_sizes[idx] else im0.copy()
                best = try_quality_search(im, per_page_targets[idx], max_q=95, min_q=5)
                if best is None:
                    best = bytes_from_jpeg_image(im, 5)
                temp_data_list.append(best)

        total_images_bytes = sum(len(d) for d in temp_data_list)
        total_estimated = total_images_bytes + overhead_estimate

        if total_estimated <= target_bytes or min(new_w, new_h) <= min_side:
            compressed_image_data_list = temp_data_list
            break

        scale *= 0.85  # shrink further and retry

    # Save compressed images
    compressed_paths = []
    for i, data in enumerate(compressed_image_data_list):
        cp = os.path.join(temp_dir, f"page_{i+1}_compressed.jpg")
        with open(cp, "wb") as f:
            f.write(data)
        compressed_paths.append(cp)

    # Rebuild PDF
    new_doc = fitz.open()
    in_doc = fitz.open(input_pdf)
    for i, comp_img in enumerate(compressed_paths):
        rect = in_doc[i].rect
        page = new_doc.new_page(width=rect.width, height=rect.height)
        page.insert_image(rect, filename=comp_img)
    in_doc.close()
    new_doc.save(out_pdf)
    new_doc.close()

    # Final exact write
    with open(out_pdf, "rb") as f:
        write_exact(out_pdf, f.read(), target_bytes)

    final_kb = os.path.getsize(out_pdf) / 1024.0
    print(f"Original: {orig_kb:.2f} KB | Target: {target_kb:.2f} KB | Final: {final_kb:.2f} KB (exact)")
    print(f"FINAL_OUTPUT_PATH::{out_pdf}")

except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)

finally:
    safe_remove(temp_dir)
