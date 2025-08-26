const express = require("express");
const multer = require("multer");
const path = require("path");
const { spawn } = require("child_process");
const fs = require("fs");

const router = express.Router();
const upload = multer({ dest: "uploads/" });

// POST /compress
router.post("/", upload.single("file"), (req, res) => {
  if (!req.file) return res.status(400).send("No file uploaded");

  const targetSizeKB = req.body.targetSizeKB || 500; // default
  const filePath = req.file.path;
  const ext = path.extname(req.file.originalname).toLowerCase();

  let script = null;
  if (ext === ".jpg" || ext === ".jpeg" || ext === ".png") {
    script = "compress_img.py";
  } else if (ext === ".pdf") {
    script = "compress_pdf.py";
  } else {
    return res.status(400).send("Unsupported file type");
  }

  const py = spawn("python", [
    path.join(__dirname, "..", "python", script),
    filePath,
    targetSizeKB
  ]);

  let output = "";
  py.stdout.on("data", data => (output += data.toString()));
  py.stderr.on("data", data => console.error("PYERR:", data.toString()));

  py.on("close", code => {
    const match = output.match(/FINAL_OUTPUT_PATH::(.+)/);
    if (!match) return res.status(500).send("Compression failed");

    const finalPath = match[1].trim();
    res.download(finalPath, path.basename(finalPath));
  });
});

module.exports = router;
