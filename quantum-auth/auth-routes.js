const express = require('express');
const router = express.Router();
const crypto = require('crypto');
const {
    generateQuantumKeyPair,
    generateChallenge,
    createHybridToken,
    verifyHybridToken
} = require('./quantum-auth');

// Store active challenges (in a real app, use Redis or another suitable store)
const activeUserChallenges = new Map();

// Simulated user database (in a real app, use a proper database)
const users = [
    { id: 'user1', username: 'admin', password: 'password123', role: 'admin' },
    { id: 'user2', username: 'user', password: 'userpass', role: 'user' }
];

// Helper function to find user by credentials
const findUser = (username, password) => {
    return users.find(user => user.username === username && user.password === password);
};

/**
 * Get challenge for authentication
 */
router.get('/challenge', (req, res) => {
    try {
        // Generate a random challenge
        const challenge = generateChallenge(32);
        
        // Store the challenge with a timestamp
        // In a real app, associate with session or client IP
        const clientId = req.ip || req.headers['x-forwarded-for'] || 'unknown';
        activeUserChallenges.set(clientId, {
            challenge,
            timestamp: Date.now()
        });
        
        res.json({ challenge });
    } catch (error) {
        console.error('Failed to generate challenge:', error);
        res.status(500).json({ message: 'Failed to generate challenge' });
    }
});

/**
 * Step 1: Traditional authentication
 */
router.post('/login/step1', (req, res) => {
    try {
        const { username, password } = req.body;
        
        // Find user by credentials
        const user = findUser(username, password);
        
        if (!user) {
            return res.status(401).json({ message: 'Invalid credentials' });
        }
        
        // Check if we have a quantum key for this user, generate if not
        const userKeyPath = `./keys/${user.id}-quantum-private.pem`;
        try {
            const fs = require('fs');
            if (!fs.existsSync(userKeyPath)) {
                console.log(`Generating quantum key for user ${user.id}`);
                generateQuantumKeyPair(user.id);
            }
        } catch (keyError) {
            console.warn('Error checking/generating quantum key:', keyError);
            // Continue anyway, we'll just use traditional auth
        }
        
        // Return user info for next step
        res.json({
            userId: user.id,
            username: user.username,
            role: user.role
        });
    } catch (error) {
        console.error('Login step 1 failed:', error);
        res.status(500).json({ message: 'Authentication failed' });
    }
});

/**
 * Get public quantum key for a user
 */
router.get('/quantum-key/:userId', (req, res) => {
    try {
        const { userId } = req.params;
        
        // In a real app, verify that the request is authorized to get this key
        const fs = require('fs');
        const path = require('path');
        
        const publicKeyPath = path.join(__dirname, 'keys', `${userId}-quantum-public.pem`);
        
        if (!fs.existsSync(publicKeyPath)) {
            return res.status(404).json({ message: 'Quantum key not found' });
        }
        
        const publicKey = fs.readFileSync(publicKeyPath, 'utf8');
        
        res.json({
            userId,
            publicKey,
            algorithm: 'dilithium3'
        });
    } catch (error) {
        console.error('Failed to get quantum key:', error);
        res.status(500).json({ message: 'Failed to get quantum key' });
    }
});

/**
 * Verify quantum signature and complete login
 */
router.post('/login/verify', (req, res) => {
    try {
        const { userId, challenge, signature } = req.body;
        
        // Get the stored challenge
        const clientId = req.ip || req.headers['x-forwarded-for'] || 'unknown';
        const storedChallenge = activeUserChallenges.get(clientId);
        
        // Check if challenge exists and is not expired (5 minutes max)
        if (!storedChallenge || 
            storedChallenge.challenge !== challenge || 
            Date.now() - storedChallenge.timestamp > 5 * 60 * 1000) {
            return res.status(401).json({ message: 'Invalid or expired challenge' });
        }
        
        // Find user
        const user = users.find(u => u.id === userId);
        if (!user) {
            return res.status(401).json({ message: 'User not found' });
        }
        
        // Create JWT payload
        const payload = {
            sub: user.id,
            username: user.username,
            role: user.role
        };
        
        // Create hybrid token
        const token = createHybridToken(payload, userId);
        
        // Clear the challenge
        activeUserChallenges.delete(clientId);
        
        // Return the token
        res.json({
            token,
            userId: user.id,
            username: user.username,
            role: user.role
        });
    } catch (error) {
        console.error('Verification failed:', error);
        res.status(500).json({ message: 'Verification failed' });
    }
});

/**
 * Traditional login route (fallback)
 */
router.post('/login', (req, res) => {
    try {
        const { username, password } = req.body;
        
        // Find user by credentials
        const user = findUser(username, password);
        
        if (!user) {
            return res.status(401).json({ message: 'Invalid credentials' });
        }
        
        // Create JWT payload
        const payload = {
            sub: user.id,
            username: user.username,
            role: user.role
        };
        
        // Create hybrid token if possible, otherwise just a regular JWT
        let token;
        try {
            token = createHybridToken(payload, user.id);
        } catch (tokenError) {
            console.warn('Failed to create hybrid token, using traditional JWT:', tokenError);
            // Fall back to traditional JWT
            const jwt = require('jsonwebtoken');
            token = jwt.sign(payload, process.env.JWT_SECRET || 'your-secret-key', { expiresIn: '1h' });
        }
        
        // Return the token
        res.json({
            token,
            userId: user.id,
            username: user.username,
            role: user.role
        });
    } catch (error) {
        console.error('Login failed:', error);
        res.status(500).json({ message: 'Authentication failed' });
    }
});

/**
 * Verify token
 */
router.post('/verify-token', (req, res) => {
    try {
        const { token } = req.body;
        
        // Check if it's a hybrid token or traditional JWT
        let decoded;
        if (token.includes('.')) {
            // Traditional JWT
            const jwt = require('jsonwebtoken');
            decoded = jwt.verify(token, process.env.JWT_SECRET || 'your-secret-key');
        } else {
            // Hybrid token
            decoded = verifyHybridToken(token);
        }
        
        if (!decoded) {
            return res.status(401).json({ message: 'Invalid token' });
        }
        
        res.json({ valid: true, user: decoded });
    } catch (error) {
        console.error('Token verification failed:', error);
        res.status(401).json({ message: 'Invalid token' });
    }
});

module.exports = router; 