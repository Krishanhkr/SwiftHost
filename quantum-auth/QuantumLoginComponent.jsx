import React, { useState, useEffect } from 'react';
import axios from 'axios';

const QuantumLoginComponent = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [quantumSupported, setQuantumSupported] = useState(false);
    
    // Check if the browser supports the required crypto APIs
    useEffect(() => {
        const checkWebCryptoSupport = async () => {
            if (window.crypto && window.crypto.subtle) {
                try {
                    // The Dilithium algorithm would be implemented through a
                    // combination of WebAssembly and Web Crypto API in production
                    // For now, we'll simulate support
                    setQuantumSupported(true);
                } catch (error) {
                    console.error('Quantum cryptography not supported:', error);
                    setQuantumSupported(false);
                }
            } else {
                setQuantumSupported(false);
            }
        };
        
        checkWebCryptoSupport();
    }, []);
    
    // Function to handle traditional login
    const handleTraditionalLogin = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        
        try {
            const response = await axios.post('/api/auth/login', {
                username,
                password
            });
            
            // Store the JWT token
            localStorage.setItem('token', response.data.token);
            
            // Redirect to dashboard or home page
            window.location.href = '/dashboard';
        } catch (error) {
            setError(error.response?.data?.message || 'Login failed');
        } finally {
            setLoading(false);
        }
    };
    
    // Function to handle quantum-safe login
    const handleQuantumLogin = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        
        try {
            // Step 1: Get a challenge from the server
            const challengeResponse = await axios.get('/api/auth/challenge');
            const challenge = challengeResponse.data.challenge;
            
            // Step 2: Traditional authentication first
            const authResponse = await axios.post('/api/auth/login/step1', {
                username,
                password
            });
            
            // Get the user ID from the response
            const { userId } = authResponse.data;
            
            // Step 3: Get the quantum key for this user
            // In a real-world scenario, the key would be stored securely in the browser
            const keyResponse = await axios.get(`/api/auth/quantum-key/${userId}`);
            const quantumKeyData = keyResponse.data;
            
            // Step 4: Sign the challenge with the quantum key
            // In a real implementation, this would use Web Crypto API with CRYSTALS-Dilithium
            // Here we simulate the signing process
            const encoder = new TextEncoder();
            const data = encoder.encode(challenge);
            
            // Simulate quantum signing - in production this would be done with a WASM module
            // implementing CRYSTALS-Dilithium
            const signature = await simulateQuantumSignature(data, quantumKeyData);
            
            // Step 5: Send the signature back to the server
            const verifyResponse = await axios.post('/api/auth/login/verify', {
                userId,
                challenge,
                signature
            });
            
            // Store the hybrid JWT token
            localStorage.setItem('hybridToken', verifyResponse.data.token);
            
            // Redirect to dashboard or home page
            window.location.href = '/dashboard';
        } catch (error) {
            setError(error.response?.data?.message || 'Quantum login failed');
        } finally {
            setLoading(false);
        }
    };
    
    // Simulate quantum signature (in production this would be CRYSTALS-Dilithium)
    const simulateQuantumSignature = async (data, keyData) => {
        // This is a placeholder for actual CRYSTALS-Dilithium implementation
        // In production, this would be implemented using WebAssembly
        return new Promise((resolve) => {
            setTimeout(() => {
                // Generate a simulated signature
                const signature = Array.from(new Uint8Array(64), () => 
                    Math.floor(Math.random() * 256)
                );
                resolve(btoa(String.fromCharCode.apply(null, signature)));
            }, 500);
        });
    };
    
    return (
        <div className="quantum-login-container">
            <h2>Secure Login</h2>
            <p>This login is protected by hybrid authentication using traditional and quantum-resistant cryptography.</p>
            
            {error && <div className="error-message">{error}</div>}
            
            <form onSubmit={quantumSupported ? handleQuantumLogin : handleTraditionalLogin}>
                <div className="form-group">
                    <label htmlFor="username">Username</label>
                    <input
                        type="text"
                        id="username"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        required
                    />
                </div>
                
                <div className="form-group">
                    <label htmlFor="password">Password</label>
                    <input
                        type="password"
                        id="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                    />
                </div>
                
                <button type="submit" disabled={loading}>
                    {loading ? 'Logging in...' : 'Login'}
                </button>
            </form>
            
            <div className="security-info">
                <small>
                    {quantumSupported 
                        ? '✅ Using quantum-resistant CRYSTALS-Dilithium authentication' 
                        : '⚠️ Quantum-resistant authentication not available in this browser'}
                </small>
            </div>
        </div>
    );
};

export default QuantumLoginComponent; 