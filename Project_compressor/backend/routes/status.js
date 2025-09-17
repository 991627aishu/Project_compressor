// routes/status.js
const express = require('express');
const router = express.Router();

router.get('/status', (req, res) => {
  const currentTime = new Date().toLocaleString();
  res.json({
    message: 'Server is on',
    time: currentTime
  });
});

module.exports = router;
