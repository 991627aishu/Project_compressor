

// const express = require('express');
// const path = require('path');
// const compressRouter = require('./routes/compress');
// const cors = require('cors');

// const app = express();
// // Use the PORT environment variable or default to 3000
// const port = process.env.PORT || 3000;

// // Enable CORS (useful if frontend is hosted separately)
// app.use(cors());

// // Middleware to parse form data and JSON
// app.use(express.urlencoded({ extended: true }));
// app.use(express.json());

// // Serve frontend static files
// app.use(express.static(path.join(__dirname, '..', 'frontend')));

// // Serve main HTML page
// app.get('/', (req, res) => {
//   res.sendFile(path.join(__dirname, '..', 'frontend', 'index.html'));
// });

// // Compression endpoint
// app.use('/compress', compressRouter);

// // ✅ NEW: Render status route
// app.get('/status', (req, res) => {
//   const currentTime = new Date().toLocaleString();
//   res.json({
//     message: 'Server is on',
//     time: currentTime
//   });
// });

// // Start server
// app.listen(port, () => {
//   console.log(`✅ Server running on http://localhost:${port}`);
// });










// const express = require('express');
// const path = require('path');
// const compressRouter = require('./routes/compress');
// const cors = require('cors');

// const app = express();
// // Use the PORT environment variable or default to 3000
// const port = process.env.PORT || 3000;

// // Enable CORS (useful if frontend is hosted separately)
// app.use(cors());

// // Middleware to parse form data and JSON
// app.use(express.urlencoded({ extended: true }));
// app.use(express.json());

// // ✅ Log every request (method, URL, time)
// app.use((req, res, next) => {
//   console.log(`[${new Date().toLocaleString()}] ${req.method} ${req.url}`);
//   next();
// });

// // Serve frontend static files
// app.use(express.static(path.join(__dirname, '..', 'frontend')));

// // Serve main HTML page
// app.get('/', (req, res) => {
//   res.sendFile(path.join(__dirname, '..', 'frontend', 'index.html'));
// });

// // Compression endpoint
// app.use('/compress', compressRouter);

// // ✅ NEW: Render status route
// app.get('/status', (req, res) => {
//   const currentTime = new Date().toLocaleString();
//   res.json({
//     message: 'Server is on',
//     time: currentTime
//   });
// });

// // Start server
// app.listen(port, () => {
//   console.log(`✅ Server running on http://localhost:${port}`);
// });














const express = require('express');
const path = require('path');
const compressRouter = require('./routes/compress');
const uploadRouter = require('./routes/upload');
const cors = require('cors');
const cron = require('node-cron');
const fs = require('fs');

const app = express();
const port = process.env.PORT || 3000;

// ✅ Upload folder path (only declare once)
const uploadDir = path.join(__dirname, '..', 'frontend', 'uploads');

// ✅ Enable CORS
app.use(cors());

// ✅ Middleware
app.use(express.urlencoded({ extended: true }));
app.use(express.json());

// ✅ Log every request
app.use((req, res, next) => {
  console.log(`[${new Date().toLocaleString()}] ${req.method} ${req.url}`);
  next();
});

// ✅ Serve frontend
app.use(express.static(path.join(__dirname, '..', 'frontend')));
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, '..', 'frontend', 'index.html'));
});

// ✅ Routes
app.use('/compress', compressRouter);
app.use('/upload', uploadRouter);
app.get('/status', (req, res) => {
  const currentTime = new Date().toLocaleString();
  res.json({ message: 'Server is on', time: currentTime });
});

// ✅ Cron job to auto-delete files
cron.schedule('*/10 * * * *', () => {
  console.log('🕒 Cron job is running...');
  console.log('📁 Scanning folder:', uploadDir);

  fs.readdir(uploadDir, (err, files) => {
    if (err) return console.error('❌ Error reading upload dir:', err);

    files.forEach(file => {
      const filePath = path.join(uploadDir, file);
      fs.stat(filePath, (err, stats) => {
        if (err) return console.error('❌ Error stating file:', err);

        const now = Date.now();
        const age = (now - stats.mtimeMs) / 1000;

        if (age > 600) { // 600 seconds = 10 minutes
          fs.unlink(filePath, err => {
            if (err) console.error('❌ Error deleting file:', err);
            else console.log(`🧹 Deleted: ${file}`);
          });
        }
      });
    });
  });
});

// ✅ Start server
app.listen(port, () => {
  console.log(`✅ Server running on http://localhost:${port}`);
});




















