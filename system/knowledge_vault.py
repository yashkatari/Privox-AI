"""
Personal Knowledge Vault for PriVox
Local encrypted long-term memory for user facts, passwords, and API keys.
"""
import json
import base64
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import os

class KnowledgeVault:
    def __init__(self):
        self.vault_file = Path("data/vault.encrypted")
        self.key_file = Path("data/.vault_key")
        self.fernet = None
        self._init_encryption()

    def _init_encryption(self):
        """Initializes local encryption key for the vault"""
        self.vault_file.parent.mkdir(exist_ok=True)
        
        # Load or generate key
        if self.key_file.exists():
            with open(self.key_file, "rb") as f:
                key = f.read()
            self.fernet = Fernet(key)
        else:
            # Generate a stable local key based on a fixed random seed for local-only use
            key = Fernet.generate_key()
            with open(self.key_file, "wb") as f:
                f.write(key)
            # hide the key file in windows
            if os.name == 'nt':
                try:
                    os.system(f"attrib +h {self.key_file}")
                except: pass
            self.fernet = Fernet(key)

    def _read_vault(self):
        if not self.vault_file.exists():
            return {}
        try:
            with open(self.vault_file, "rb") as f:
                encrypted_data = f.read()
            decrypted_data = self.fernet.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode("utf-8"))
        except Exception as e:
            print(f"[Knowledge Vault Error] Failed to read: {e}")
            return {}

    def _write_vault(self, data: dict):
        try:
            json_str = json.dumps(data)
            encrypted_data = self.fernet.encrypt(json_str.encode("utf-8"))
            with open(self.vault_file, "wb") as f:
                f.write(encrypted_data)
            return True
        except Exception as e:
            print(f"[Knowledge Vault Error] Failed to write: {e}")
            return False

    def remember(self, user_intent):
        """
        Parses "remember that my wife's name is Sarah"
        or "save my wifi password as 12345"
        """
        trigger_phrases = ["remember that", "remember", "save", "keep in mind that"]
        clean_text = user_intent.lower()
        
        for trigger in trigger_phrases:
            if trigger in clean_text:
                # Naive extraction - just store the rest of the sentence
                fact = user_intent[clean_text.find(trigger) + len(trigger):].strip()
                if fact:
                    vault = self._read_vault()
                    import time
                    fact_id = str(int(time.time()))
                    vault[fact_id] = fact
                    self._write_vault(vault)
                    return True, f"I have securely remembered: '{fact}'"
        
        return False, ""

    def recall(self, user_intent):
        """
        Searches the vault for facts matching the query.
        e.g., "what is my wifi password" -> searches for 'wifi' and 'password'
        """
        vault = self._read_vault()
        if not vault:
            return False, ""
            
        clean_text = user_intent.lower()
        # Find non-stop words
        keywords = [word for word in clean_text.split() if len(word) > 3 and word not in ["what", "when", "where", "who", "tell", "me", "remember", "recall"]]
        
        if not keywords:
            return False, ""

        matches = []
        for fact_id, fact in vault.items():
            fact_lower = fact.lower()
            if any(kw in fact_lower for kw in keywords):
                matches.append(fact)
                
        if matches:
            response = "\n".join([f"• {m}" for m in matches])
            return True, f"Here is what I remember about that:\n{response}"
            
        return False, ""

# Global instance
knowledge_vault = KnowledgeVault()
