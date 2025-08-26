const express = require('express');
const path = require('path');
const compressRouter = require('./routes/compress');
const cors = require('cors');

const app = express();
const port = 3000;

// CORS (needed if frontend hosted separately)
app.use(cors());

// Middleware to parse form data and JSON
app.use(express.urlencoded({ extended: true }));
app.use(express.json());

// Serve frontend static files
app.use(express.static(path.join(__dirname, '..', 'frontend')));

// Serve main HTML page
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, '..', 'frontend', 'index.html'));
});

// Use compress router for compression endpoint
app.use('/compress', compressRouter);

// Start server
app.listen(port, () => {
  console.log(`✅ Server running on http://localhost:${port}`);
});
