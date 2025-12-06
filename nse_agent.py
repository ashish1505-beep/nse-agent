import os
import sys

print("🤖 NSE Agent starting...")

# TEMPORARY: Hardcode for testing
# Replace these with YOUR actual values
GROK_API_KEY = os.getenv('GROK_API_KEY', 'xai-Am8JzhcBk3vBM9AOejQmFUrm29F5ou8W9ClFyz8csUTakaNMRmNH6C2Cmd1FsLJaraKkH7Sus2twvBMw')
EMAIL_USER = os.getenv('EMAIL_USER', 'ashish1505@gmail.com')
EMAIL_PASS = os.getenv('EMAIL_PASS', 'ftnz aznu beuk kqvb')

print(f"GROK: {'OK' if GROK_API_KEY and 'gsk_' in GROK_API_KEY else 'MISSING'}")
print(f"EMAIL_USER: {'OK' if '@' in str(EMAIL_USER) else 'MISSING'}")
print(f"EMAIL_PASS: {'OK' if EMAIL_PASS and len(EMAIL_PASS) > 5 else 'MISSING'}")

if not (GROK_API_KEY and EMAIL_USER and EMAIL_PASS):
    print("❌ ERROR: Secrets incomplete!")
    print(f"  GROK_API_KEY: {GROK_API_KEY[:20]}...")
    print(f"  EMAIL_USER: {EMAIL_USER}")
    print(f"  EMAIL_PASS: {'*' * len(str(EMAIL_PASS))}")
    sys.exit(1)

print("✅ All secrets OK - Sending test email...")

import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import pytz

ist = pytz.timezone('Asia/Kolkata')

msg = MIMEText("✅ NSE Agent is WORKING!")
msg['Subject'] = f'NSE Test - {datetime.now(ist).strftime("%d/%m %H:%M")}'
msg['From'] = EMAIL_USER
msg['To'] = EMAIL_USER

try:
    print(f"📧 Connecting to Gmail...")
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    print(f"🔐 Logging in as {EMAIL_USER}...")
    server.login(EMAIL_USER, EMAIL_PASS)
    print(f"📤 Sending email...")
    server.send_message(msg)
    server.quit()
    print("✅ EMAIL SENT SUCCESSFULLY!")
except Exception as e:
    print(f"❌ EMAIL ERROR: {e}")
    sys.exit(1)

print("🎉 TEST COMPLETE!")
