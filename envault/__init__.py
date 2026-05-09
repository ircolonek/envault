"""envault — Secure environment variable manager.

Encrypts .env files using AES-256-GCM and syncs them across team members
via a shared backend.
"""

__version__ = "0.1.0"
__author__ = "envault contributors"

from envault.crypto import encrypt, decrypt

__all__ = ["encrypt", "decrypt"]
