#!/usr/bin/env python3
import base64
import secrets

print(f"SECRET_KEY={secrets.token_urlsafe(48)}")
print(f"ENCRYPTION_KEY={base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()}")
