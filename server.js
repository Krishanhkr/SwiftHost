const express = require('express');
const helmet = require('helmet');
const compression = require('compression');
const cors = require('cors');
const path = require('path');
const http = require('http');
const { Server } = require('socket.io');

// Create Express app
const app = express();
const server = http.createServer(app);
const io = new Server(server);
const port = process.env.PORT || 3000;

// Basic middleware
app.use(compression());
app.use(cors());

// Simplified security headers
app.use(
  helmet({
    contentSecurityPolicy: false, // Disable CSP for now
    crossOriginEmbedderPolicy: false,
    crossOriginResourcePolicy: false,
    crossOriginOpenerPolicy: false,
  })
);

// Static files middleware - set caching headers
app.use(express.static(path.join(__dirname, './'), {
  maxAge: '1h', // Cache for 1 hour
  etag: true,
}));

// Routes
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

// API simulation for domain check
app.get('/api/check-domain', (req, res) => {
  const domain = req.query.q;
  
  if (!domain) {
    return res.status(400).json({ error: 'Domain is required' });
  }
  
  // Simulate API delay
  setTimeout(() => {
    // Generate random result for demo
    const available = Math.random() > 0.3;
    const price = `$${(Math.random() * 10 + 9.99).toFixed(2)}`;
    
    res.json({
      domain,
      available,
      price
    });
  }, 500);
});

// Simulate server stats for monitoring
const generateServerStats = () => {
  return {
    timestamp: new Date().toISOString(),
    cpu: Math.floor(Math.random() * 100),
    memory: Math.floor(Math.random() * 100),
    disk: Math.floor(Math.random() * 100),
    network: Math.floor(Math.random() * 1000),
    requests: Math.floor(Math.random() * 200),
    uptime: 99.95 + (Math.random() * 0.05)
  };
};

// Socket.IO connection
io.on('connection', (socket) => {
  console.log('Client connected: ' + socket.id);
  
  // Send real-time updates every 2 seconds (less frequent)
  const interval = setInterval(() => {
    socket.emit('stats-update', generateServerStats());
  }, 2000);
  
  // Handle disconnection
  socket.on('disconnect', () => {
    console.log('Client disconnected: ' + socket.id);
    clearInterval(interval);
  });
});

// Start server
server.listen(port, () => {
  console.log(`Server running at http://localhost:${port}`);
  console.log(`Visit http://localhost:${port} to view the site`);
});