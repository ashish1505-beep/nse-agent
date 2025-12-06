import os

GROK_API_KEY = os.getenv('GROK_API_KEY', '')
EMAIL_USER = os.getenv('EMAIL_USER', '')
EMAIL_PASS = os.getenv('EMAIL_PASS', '')

# TEMPORARY DEBUG - Shows FIRST 5 chars to verify
print(f"GROK key starts with: {GROK_API_KEY[:15]}...")
print(f"EMAIL_USER is: {EMAIL_USER}")
print(f"EMAIL_PASS length: {len(EMAIL_PASS)} chars")
