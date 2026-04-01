#!/usr/bin/env python3
"""
Generate JWKS from your public key for Canvas LTI configuration
Usage: python generate_jwks.py <public_key.pem> [kid]
"""

import sys
import json
import base64
import hashlib
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

def generate_jwks(public_key_path, kid=None):
    try:
        # Load the public key
        with open(public_key_path, 'rb') as f:
            public_key_pem = f.read()
            public_key = serialization.load_pem_public_key(
                public_key_pem,
                backend=default_backend()
            )
        
        # Extract the public numbers
        numbers = public_key.public_numbers()
        
        # Helper function to convert int to base64url
        def to_base64url(num):
            byte_len = (num.bit_length() + 7) // 8
            num_bytes = num.to_bytes(byte_len, byteorder='big')
            encoded = base64.urlsafe_b64encode(num_bytes).decode('utf-8')
            return encoded.rstrip('=')  # Remove padding
        
        # Generate kid if not provided
        # Using SHA256 hash of the public key (common practice)
        if kid is None:
            key_hash = hashlib.sha256(public_key_pem).digest()
            kid = base64.urlsafe_b64encode(key_hash[:16]).decode('utf-8').rstrip('=')
        
        # Build the JWK
        jwk = {
            "kty": "RSA",
            "e": to_base64url(numbers.e),
            "n": to_base64url(numbers.n),
            "alg": "RS256",
            "kid": kid,
            "use": "sig"
        }
        
        return jwk
        
    except FileNotFoundError:
        print(f"Error: Could not find file '{public_key_path}'")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python generate_jwks.py <public_key.pem> [kid]")
        print("\nExamples:")
        print("  python generate_jwks.py public_key.pem")
        print("  python generate_jwks.py public_key.pem my-custom-key-id")
        sys.exit(1)
    
    public_key_file = sys.argv[1]
    custom_kid = sys.argv[2] if len(sys.argv) == 3 else None
    
    jwks = generate_jwks(public_key_file, custom_kid)
    
    print("\n" + "="*60)
    print("Copy this JSON and paste it into Canvas public_jwk field:")
    print("="*60 + "\n")
    print(json.dumps(jwks, indent=2))
    print("\n" + "="*60)
    print(f"\n✓ Key ID (kid): {jwks['kid']}")
    if custom_kid is None:
        print("  (auto-generated from key fingerprint)")
    print("\n IMPORTANT: If you specify a 'kid' when signing JWTs,")
    print("   it must match this value!")
    print("="*60)
