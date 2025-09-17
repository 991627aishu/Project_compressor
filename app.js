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
const express = require('express');
const path = require('path');
const compressRouter = require('./routes/compress');
const cors = require('cors');

const app = express();
// Use the PORT environment variable or default to 3000
const port = process.env.PORT || 3000;

// Enable CORS (useful if frontend is hosted separately)
app.use(cors());

// Middleware to parse form data and JSON
app.use(express.urlencoded({ extended: true }));
app.use(express.json());

// ✅ Log every request (method, URL, time)
app.use((req, res, next) => {
  console.log(`[${new Date().toLocaleString()}] ${req.method} ${req.url}`);
  next();
});

// Serve frontend static files
app.use(express.static(path.join(__dirname, '..', 'frontend')));

// Serve main HTML page
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, '..', 'frontend', 'index.html'));
});

// Compression endpoint
app.use('/compress', compressRouter);

// ✅ NEW: Render status route
app.get('/status', (req, res) => {
  const currentTime = new Date().toLocaleString();
  res.json({
    message: 'Server is on',
    time: currentTime
  });
});

// Start server
app.listen(port, () => {
  console.log(`✅ Server running on http://localhost:${port}`);
});
