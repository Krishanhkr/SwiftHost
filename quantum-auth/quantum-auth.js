const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const jwt = require('jsonwebtoken');
const { execSync } = require('child_process');

// Configuration
const JWT_SECRET = process.env.JWT_SECRET || 'your-secret-key';
const JWT_EXPIRES_IN = '1h';
const QUANTUM_KEY_DIR = path.join(__dirname, 'keys');

// Ensure key directory exists
if (!fs.existsSync(QUANTUM_KEY_DIR)) {
    fs.mkdirSync(QUANTUM_KEY_DIR, { recursive: true });
}

/**
 * Generate quantum-safe key pair using CRYSTALS-Dilithium
 * @param {string} userId - User ID to associate with the key
 * @returns {Object} Key information
 */
function generateQuantumKeyPair(userId) {
    // Create keys directory if it doesn't exist
    if (!fs.existsSync(QUANTUM_KEY_DIR)) {
        fs.mkdirSync(QUANTUM_KEY_DIR, { recursive: true });
    }

    const privateKeyPath = path.join(QUANTUM_KEY_DIR, `${userId}-quantum-private.pem`);
    const publicKeyPath = path.join(QUANTUM_KEY_DIR, `${userId}-quantum-public.pem`);

    try {
        // Generate dilithium key pair using OpenSSL
        execSync(`openssl genpkey -algorithm dilithium3 -out ${privateKeyPath}`);
        execSync(`openssl pkey -in ${privateKeyPath} -pubout -out ${publicKeyPath}`);

        return {
            userId,
            privateKeyPath,
            publicKeyPath,
            algorithm: 'dilithium3'
        };
    } catch (error) {
        console.error('Failed to generate quantum key pair:', error);
        throw new Error('Failed to generate quantum key pair');
    }
}

/**
 * Sign data using quantum-safe signature
 * @param {string} userId - User ID associated with the key
 * @param {string} data - Data to sign
 * @returns {string} Base64 encoded signature
 */
function quantumSign(userId, data) {
    const privateKeyPath = path.join(QUANTUM_KEY_DIR, `${userId}-quantum-private.pem`);
    
    if (!fs.existsSync(privateKeyPath)) {
        throw new Error(`Quantum private key not found for user ${userId}`);
    }
    
    try {
        // Create a temporary file with the data
        const tempDataPath = path.join(QUANTUM_KEY_DIR, `${userId}-temp-data.txt`);
        fs.writeFileSync(tempDataPath, data);
        
        // Sign the data using OpenSSL
        const signaturePath = path.join(QUANTUM_KEY_DIR, `${userId}-signature.bin`);
        execSync(`openssl pkeyutl -sign -inkey ${privateKeyPath} -in ${tempDataPath} -out ${signaturePath}`);
        
        // Read the signature and encode it as base64
        const signature = fs.readFileSync(signaturePath);
        const base64Signature = signature.toString('base64');
        
        // Clean up temporary files
        fs.unlinkSync(tempDataPath);
        fs.unlinkSync(signaturePath);
        
        return base64Signature;
    } catch (error) {
        console.error('Failed to sign data with quantum key:', error);
        throw new Error('Failed to sign data with quantum key');
    }
}

/**
 * Verify data using quantum-safe signature
 * @param {string} userId - User ID associated with the key
 * @param {string} data - Original data
 * @param {string} signature - Base64 encoded signature
 * @returns {boolean} Whether the signature is valid
 */
function quantumVerify(userId, data, signature) {
    const publicKeyPath = path.join(QUANTUM_KEY_DIR, `${userId}-quantum-public.pem`);
    
    if (!fs.existsSync(publicKeyPath)) {
        throw new Error(`Quantum public key not found for user ${userId}`);
    }
    
    try {
        // Create temporary files
        const tempDataPath = path.join(QUANTUM_KEY_DIR, `${userId}-temp-data.txt`);
        const signaturePath = path.join(QUANTUM_KEY_DIR, `${userId}-signature.bin`);
        
        // Write data and signature to temporary files
        fs.writeFileSync(tempDataPath, data);
        fs.writeFileSync(signaturePath, Buffer.from(signature, 'base64'));
        
        // Verify the signature using OpenSSL
        try {
            execSync(`openssl pkeyutl -verify -pubin -inkey ${publicKeyPath} -in ${tempDataPath} -sigfile ${signaturePath}`);
            return true;
        } catch (error) {
            return false;
        } finally {
            // Clean up temporary files
            fs.unlinkSync(tempDataPath);
            fs.unlinkSync(signaturePath);
        }
    } catch (error) {
        console.error('Failed to verify quantum signature:', error);
        throw new Error('Failed to verify quantum signature');
    }
}

/**
 * Generate a random challenge for authentication
 * @param {number} length - Length of the challenge in bytes
 * @returns {string} Base64 encoded challenge
 */
function generateChallenge(length = 32) {
    return crypto.randomBytes(length).toString('base64');
}

/**
 * Create a hybrid JWT with quantum-safe signature
 * @param {Object} payload - JWT payload
 * @param {string} userId - User ID
 * @returns {string} Hybrid JWT token
 */
function createHybridToken(payload, userId) {
    // Create traditional JWT
    const traditionalJwt = jwt.sign(payload, JWT_SECRET, { expiresIn: JWT_EXPIRES_IN });
    
    // Add quantum signature
    const quantumSignature = quantumSign(userId, traditionalJwt);
    
    // Create hybrid token
    const hybridToken = {
        jwt: traditionalJwt,
        quantum_sig: quantumSignature,
        user_id: userId,
        algorithm: 'dilithium3'
    };
    
    return Buffer.from(JSON.stringify(hybridToken)).toString('base64');
}

/**
 * Verify and decode a hybrid JWT
 * @param {string} token - Hybrid JWT token
 * @returns {Object} Decoded payload or null if invalid
 */
function verifyHybridToken(token) {
    try {
        // Decode hybrid token
        const hybridTokenJson = Buffer.from(token, 'base64').toString('utf8');
        const hybridToken = JSON.parse(hybridTokenJson);
        
        // Extract components
        const { jwt: traditionalJwt, quantum_sig: quantumSignature, user_id: userId } = hybridToken;
        
        // Verify traditional JWT
        const decoded = jwt.verify(traditionalJwt, JWT_SECRET);
        
        // Verify quantum signature
        const isQuantumValid = quantumVerify(userId, traditionalJwt, quantumSignature);
        
        if (!isQuantumValid) {
            throw new Error('Invalid quantum signature');
        }
        
        return decoded;
    } catch (error) {
        console.error('Failed to verify hybrid token:', error);
        return null;
    }
}

module.exports = {
    generateQuantumKeyPair,
    quantumSign,
    quantumVerify,
    generateChallenge,
    createHybridToken,
    verifyHybridToken
}; 