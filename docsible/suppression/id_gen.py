"""Short unique ID generation for suppression rules."""

import hashlib
import time
import uuid


def generate_rule_id(pattern: str) -> str:
    """Generate a unique 8-char hex ID from pattern + entropy."""
    salt = str(uuid.uuid4())
    raw = f"{pattern}:{salt}:{time.time()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:8]
