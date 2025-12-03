"""
UATP Capsule Core Implementation
"""
import json
from datetime import datetime
from .crypto import sign_data, generate_key_pair


class Capsule:
    """
    Atomic unit of trust in UATP protocol
    """

    def __init__(self, content, parent=None, author=None):
        self.content = content
        self.parent = parent  # Parent capsule hash
        self.timestamp = datetime.utcnow().isoformat()
        self.author = author or generate_key_pair()
        self.signature = None
        self.metadata = {
            "protocol_version": "1.0",
            "content_type": type(content).__name__,
        }

    def encapsulate(self):
        """Seal capsule with cryptographic signature"""
        payload = {
            "content": self.content,
            "parent": self.parent,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }
        serialized = json.dumps(payload, sort_keys=True)
        self.signature = sign_data(serialized, self.author["private_key"])
        return {
            "payload": payload,
            "signature": self.signature,
            "public_key": self.author["public_key"],
        }

    def verify(self):
        """Validate capsule integrity and ancestry"""
        # Verification logic would go here
        pass
