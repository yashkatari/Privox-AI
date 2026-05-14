
from cryptography.fernet import Fernet
import json
import base64
import os
from pathlib import Path

class SimpleE2EEncryption:
    def __init__(self, key_path="data/secret.key"):
        """
        Initialize encryption with a stored key
        If no key exists, generate a new one
        """
        self.key_path = Path(key_path)
        self.key_path.parent.mkdir(exist_ok=True)
        
        # Load or generate key
        if self.key_path.exists():
            with open(self.key_path, 'rb') as f:
                self.key = f.read()
        else:
            self.key = Fernet.generate_key()
            with open(self.key_path, 'wb') as f:
                f.write(self.key)
        
        self.cipher = Fernet(self.key)
    
    def encrypt_data(self, data):
        """Encrypt any data (converts to JSON first)"""
        if isinstance(data, (dict, list)):
            data_str = json.dumps(data)
        else:
            data_str = str(data)
        
        encrypted_bytes = self.cipher.encrypt(data_str.encode())
        return base64.urlsafe_b64encode(encrypted_bytes).decode()
    
    def decrypt_data(self, encrypted_text):
        """Decrypt data back to original format"""
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_text.encode())
            decrypted_bytes = self.cipher.decrypt(encrypted_bytes)
            decrypted_str = decrypted_bytes.decode()
            
            # Try to parse as JSON
            try:
                return json.loads(decrypted_str)
            except:
                return decrypted_str
        except Exception as e:
            print(f"[Encryption Error] {e}")
            return None
    
    def get_public_key_fingerprint(self):
        """Get a fingerprint for verification"""
        import hashlib
        return hashlib.sha256(self.key).hexdigest()[:16]

# Test function
if __name__ == "__main__":
    e2e = SimpleE2EEncryption()
    
    test_data = {
        "chat_name": "Test Chat",
        "messages": [
            {"role": "user", "content": "Hello"},
            {"role": "ai", "content": "Hi there!"}
        ],
        "timestamp": "2024-01-01T12:00:00"
    }
    
    print(f"Original: {test_data}")
    encrypted = e2e.encrypt_data(test_data)
    print(f"Encrypted: {encrypted[:50]}...")
    
    decrypted = e2e.decrypt_data(encrypted)
    print(f"Decrypted: {decrypted}")
    
    print(f"Key Fingerprint: {e2e.get_public_key_fingerprint()}")
