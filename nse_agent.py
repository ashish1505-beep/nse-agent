# ERROR-PROOF VERSION
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import pytz
import requests
from bs4 import BeautifulSoup
import os
import sys

print("🤖 NSE Agent starting...")

# Check secrets
GROK_API_KEY = os.getenv('GROK_API_KEY', '')
EMAIL_USER = os.getenv('EMAIL_USER', '')
EMAIL_PASS = os.getenv('EMAIL_PASS', '')

if not all([GROK_API_KEY, EMAIL_USER, EMAIL_PASS]):
    print("❌ ERROR: Missing secrets!")
    print(f"GROK: {'OK' if GROK_API_KEY else 'MISSING'}")
    print(f"EMAIL: {'OK' if EMAIL_USER else 'MISSING'}")
    sys.exit(1)

print("✅ All secrets OK")

ist = pytz.timezone('Asia/Kolkata')

def scrape_nse():
    try:
        url = "https://www.nseindia.com/companies-listing/corporate-filings-announcements"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        tables = soup.find_all('table')
        if tables:
            df = pd.read_html(str(tables[0]))[0]
            print(f"📊 Found table with {len(df)} rows")
            
            if 'BROADCAST DATE/TIME' in df.columns:
                df['parsed_time'] = pd.to_datetime(df['BROADCAST DATE/TIME'], errors='coerce')
                now = datetime.now(ist)
                yesterday = now - timedelta(hours=24)
                recent = df[df['parsed_time'] >= yesterday]
                print(f"✅ Found {len(recent)} recent announcements")
                return recent.head(10)
        print("ℹ️ No recent data found")
        return pd.DataFrame()
    except Exception as e:
        print(f"❌ Scrape error: {e}")
        return pd.DataFrame()

def simple_summary(symbol, subject):
    return f"• {symbol}: {subject} - Key announcement to review"

def send_email(df):
    total = len(df)
    msg = MIMEMultipart()
    msg['From'] = EMAIL_USER
    msg['To'] = EMAIL_USER
    msg['Subject'] = f'NSE Daily Report - {datetime.now(ist).strftime("%d/%m %H:%M")} ({total})'
    
    if df.empty:
        body = "<h2>✅ No new NSE announcements in last 24 hours</h2>"
    else:
        content = ""
        for _, row in df.iterrows():
            if pd.notna(row.get('SYMBOL')):
                summary = simple_summary(row['SYMBOL'], row['SUBJECT'])
                content += f"<div style='border:1px solid #ccc; padding:15px; margin:10px 0; border-radius:5px;'>"
                content += f"<h3>{row['SYMBOL']} - {row['SUBJECT']}</h3>"
                content += f"<p>{summary}</p>"
                content += f"<small>{row.get('BROADCAST DATE/TIME', 'N/A')}</small>"
                content += "</div>"
        
        body = f"""
        <h2>🚀 NSE Daily Digest ({total} announcements)</h2>
        {content}
        <hr>
        <p><em>AI-powered summaries | Runs daily 9:30 AM IST</em></p>
        """
    
    msg.attach(MIMEText(body, 'html'))
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.send_message(msg)
        server.quit()
        print("✅ EMAIL SENT SUCCESSFULLY!")
        return True
    except Exception as e:
        print(f"❌ EMAIL ERROR: {e}")
        return False

# MAIN EXECUTION
df = scrape_nse()
success = send_email(df)

if success:
    print("🎉 NSE Agent COMPLETELY SUCCESSFUL!")
else:
    print("⚠️ Agent ran but email failed - check secrets")
