import sys
import os
import io
from PIL import Image

# -------------------------
# Args
# -------------------------
if len(sys.argv) < 3:
    print("Usage: python compress_img.py <filename> <target_size_kb>")
    sys.exit(1)

filename = sys.argv[1]

try:
    target_size_kb = float(sys.argv[2])
except Exception:
    print("ERROR: target_size_kb must be a number")
    sys.exit(1)

target_bytes = int(round(target_size_kb * 1024))

# -------------------------
# Output folder (uploads/compressed/)
# -------------------------
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUTPUT_DIR = os.path.join(BASE_DIR, "uploads", "compressed")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# -------------------------
# Load image
# -------------------------
try:
    img = Image.open(filename)
except Exception as e:
    print(f"ERROR: Could not open image: {e}")
    sys.exit(1)

if img.mode in ("RGBA", "P"):
    img = img.convert("RGB")

orig_bytes = os.path.getsize(filename)
orig_kb = orig_bytes / 1024.0

# -------------------------
# Prepare output path
# -------------------------
base_name = os.path.basename(filename)
name_only = os.path.splitext(base_name)[0]
compressed_path = os.path.join(OUTPUT_DIR, f"{name_only}.jpg")

# -------------------------
# Helper functions
# -------------------------
def save_jpeg_bytes(im, quality: int) -> bytes:
    """Save PIL Image as JPEG bytes with given quality."""
    buf = io.BytesIO()
    im.save(buf, format="JPEG", optimize=True, quality=int(quality))
    return buf.getvalue()

def try_quality_search(im, max_q=95, min_q=5, target=target_bytes):
    """Binary search JPEG quality to get <= target bytes."""
    low, high = min_q, max_q
    best = None
    while low <= high:
        mid = (low + high) // 2
        data = save_jpeg_bytes(im, mid)
        size = len(data)
        if size <= target:
            best = data  # under target, keep this
            low = mid + 1
        else:
            high = mid - 1
    return best

def write_exact(path, data, exact_size):
    """Write data and pad with zeros to reach exact_size bytes (if needed)."""
    with open(path, "wb") as f:
        f.write(data)
    cur = os.path.getsize(path)
    if cur < exact_size:
        pad = exact_size - cur
        with open(path, "ab") as f:
            f.write(b"\x00" * pad)

# -------------------------
# Main compression logic
# -------------------------

# Case 1: Target >= original size → just save high quality and pad
if target_bytes >= orig_bytes:
    data = save_jpeg_bytes(img, 95)
    if len(data) > target_bytes:
        data = try_quality_search(img, max_q=95, min_q=5, target=target_bytes) or save_jpeg_bytes(img, 5)
    write_exact(compressed_path, data, target_bytes)
    final_kb = os.path.getsize(compressed_path) / 1024.0
    print(f"Original: {orig_kb:.2f} KB | Target: {target_size_kb:.2f} KB | Final: {final_kb:.2f} KB (exact)")
    print(f"FINAL_OUTPUT_PATH::{compressed_path}")
    sys.exit(0)

# Case 2: Need to compress below original size
scale = 1.0
min_side = 64  # prevent excessive shrinking
best_data = None

while True:
    w, h = img.size
    new_w, new_h = max(min_side, int(w * scale)), max(min_side, int(h * scale))
    work = img if (new_w == w and new_h == h) else img.resize((new_w, new_h), Image.LANCZOS)

    data = try_quality_search(work, max_q=95, min_q=5, target=target_bytes)
    if data is not None:
        best_data = data
        break  # success

    if new_w <= min_side or new_h <= min_side:
        best_data = save_jpeg_bytes(work, 5)
        break

    scale *= 0.9  # reduce by 10% and retry

# Extra safety: if still bigger, force another downscale
if len(best_data) > target_bytes:
    w, h = img.size
    work = img.resize((max(min_side, int(w * scale * 0.9)),
                       max(min_side, int(h * scale * 0.9))), Image.LANCZOS)
    best_data = save_jpeg_bytes(work, 5)

# Write final output (padded to exact target size)
write_exact(compressed_path, best_data, target_bytes)
final_bytes = os.path.getsize(compressed_path)
final_kb = final_bytes / 1024.0

print(f"Original: {orig_kb:.2f} KB | Target: {target_size_kb:.2f} KB | Final: {final_kb:.2f} KB (exact)")
print(f"FINAL_OUTPUT_PATH::{compressed_path}")
