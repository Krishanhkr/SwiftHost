#!/bin/bash

# Generate quantum-safe keys for authentication

echo "Generating quantum-safe keys for authentication..."

# Create required directories
mkdir -p quantum-auth/keys

# Check for OpenSSL with quantum-safe algorithms
if openssl list -public-key-algorithms | grep -q "DILITHIUM"; then
    echo "OpenSSL with CRYSTALS-Dilithium support found!"
    USE_OPENSSL=true
else
    echo "OpenSSL with CRYSTALS-Dilithium support not found. Using fallback method."
    USE_OPENSSL=false
fi

# Generate quantum-safe keys for test users
generate_keys() {
    local user_id=$1
    
    echo "Generating keys for user: $user_id"
    
    if [ "$USE_OPENSSL" = true ]; then
        # Use OpenSSL with CRYSTALS-Dilithium
        openssl genpkey -algorithm dilithium3 -out quantum-auth/keys/${user_id}-quantum-private.pem
        openssl pkey -in quantum-auth/keys/${user_id}-quantum-private.pem -pubout -out quantum-auth/keys/${user_id}-quantum-public.pem
    else
        # Fallback: Create simulated keys (for development/testing only)
        echo "-----BEGIN PRIVATE KEY-----" > quantum-auth/keys/${user_id}-quantum-private.pem
        echo "SIMULATED DILITHIUM PRIVATE KEY" >> quantum-auth/keys/${user_id}-quantum-private.pem
        echo "THIS IS NOT A REAL KEY - FOR DEVELOPMENT ONLY" >> quantum-auth/keys/${user_id}-quantum-private.pem
        dd if=/dev/urandom bs=64 count=8 2>/dev/null | base64 >> quantum-auth/keys/${user_id}-quantum-private.pem
        echo "-----END PRIVATE KEY-----" >> quantum-auth/keys/${user_id}-quantum-private.pem
        
        echo "-----BEGIN PUBLIC KEY-----" > quantum-auth/keys/${user_id}-quantum-public.pem
        echo "SIMULATED DILITHIUM PUBLIC KEY" >> quantum-auth/keys/${user_id}-quantum-public.pem
        echo "THIS IS NOT A REAL KEY - FOR DEVELOPMENT ONLY" >> quantum-auth/keys/${user_id}-quantum-public.pem
        dd if=/dev/urandom bs=64 count=4 2>/dev/null | base64 >> quantum-auth/keys/${user_id}-quantum-public.pem
        echo "-----END PUBLIC KEY-----" >> quantum-auth/keys/${user_id}-quantum-public.pem
    fi
    
    echo "Generated quantum-safe keys for user: $user_id"
}

# Generate keys for test users
generate_keys "user1"
generate_keys "user2"
generate_keys "admin"

echo "Setting appropriate permissions..."
chmod 600 quantum-auth/keys/*-private.pem
chmod 644 quantum-auth/keys/*-public.pem

echo "Quantum-safe keys generated successfully!" 