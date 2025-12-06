import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import pytz
import requests
import os
from time import sleep
from io import StringIO
import re

ist = pytz.timezone('Asia/Kolkata')
GROK_API_KEY = os.getenv('GROK_API_KEY')
GMAIL_USER = os.getenv('GMAIL_USER')
GMAIL_PASS = os.getenv('GMAIL_PASS')

def scrape_nse():
    print("📊 Scraping NSE website...")
    try:
        url = "https://www.nseindia.com/companies-listing/corporate-filings-announcements"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            print(f"Error: {response.status_code}")
            return []
        
        # Parse HTML directly with regex
        html = response.text
        
        # Extract table rows
        announcements = []
        
        # Find all rows with SYMBOL, COMPANY NAME, SUBJECT pattern
        # Simple extraction from HTML
        rows = re.findall(r'<tr[^>]*>.*?</tr>', html, re.DOTALL)
        
        for row in rows[:30]:
            try:
                # Extract cells
                cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
                
                if len(cells) >= 3:
                    symbol = cells[0].strip()
                    company = cells[1].strip() if len(cells) > 1 else "N/A"
                    subject = cells[2].strip() if len(cells) > 2 else "N/A"
                    details = cells[3].strip() if len(cells) > 3 else "N/A"
                    time_str = cells[4].strip() if len(cells) > 4 else "N/A"
                    
                    # Clean HTML tags
                    symbol = re.sub(r'<[^>]+>', '', symbol)
                    company = re.sub(r'<[^>]+>', '', company)
                    subject = re.sub(r'<[^>]+>', '', subject)
                    details = re.sub(r'<[^>]+>', '', details)
                    
                    if symbol and len(symbol) > 0:
                        announcements.append({
                            'SYMBOL': symbol[:20],
                            'COMPANY': company[:50],
                            'SUBJECT': subject[:50],
                            'DETAILS': details[:200],
                            'TIME': time_str[:20]
                        })
            except:
                continue
        
        print(f"✅ Found {len(announcements)} announcements")
        return announcements
    
    except Exception as e:
        print(f"Scrape error: {e}")
        return []

def grok_summarize(text, context=""):
    if not GROK_API_KEY:
        return "Key announcement"
    
    headers = {
        'Authorization': f'Bearer {GROK_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    prompt = f"Summarize (2 bullets, 30 words): {context} - {text[:300]}"
    
    data = {
        "model": "grok-beta",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 60,
        "temperature": 0.1
    }
    
    try:
        response = requests.post('https://api.x.ai/v1/chat/completions', 
                                headers=headers, json=data, timeout=10)
        result = response.json()
        return result['choices'][0]['message']['content'].strip()[:100]
    except:
        return f"{context}: Key announcement"

def send_email(announcements):
    total = len(announcements)
    
    if total == 0:
        body = "<h1>✅ No new NSE announcements</h1>"
    else:
        rows = ""
        for item in announcements[:15]:
            summary = grok_summarize(item['DETAILS'], item['SUBJECT'])
            rows += f"""<tr style="border-bottom: 1px solid #ddd;">
                <td style="padding: 10px; font-weight: bold; font-size: 14px;">{item['SYMBOL']}</td>
                <td style="padding: 10px; font-size: 13px;">{item['SUBJECT']}</td>
                <td style="padding: 10px; font-size: 12px; color: #1e40af;">{summary}</td>
                <td style="padding: 10px; font-size: 11px; color: #666;">{item['TIME']}</td>
            </tr>"""
            sleep(0.2)
        
        body = f"""<html><body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5;">
            <div style="max-width: 900px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px;">
                <h1 style="color: #1e40af; margin: 0 0 10px 0;">🚀 NSE Daily Digest</h1>
                <p style="color: #666; margin: 0 0 20px 0;">{datetime.now(ist).strftime("%d/%m/%Y %H:%M")} IST | {total} announcements analyzed</p>
                
                <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                    <thead>
                        <tr style="background: #1e40af; color: white;">
                            <th style="padding: 12px; text-align: left;">STOCK</th>
                            <th style="padding: 12px; text-align: left;">SUBJECT</th>
                            <th style="padding: 12px; text-align: left;">AI SUMMARY</th>
                            <th style="padding: 12px; text-align: left;">TIME</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows}
                    </tbody>
                </table>
                
                <p style="color: #999; font-size: 12px; margin: 0;">Watchlist: RELIANCE, KPITTECH, JTLIND, MOTILALOFS | Daily 9:30 AM IST</p>
            </div>
        </body></html>"""
    
    msg = MIMEMultipart()
    msg['From'] = GMAIL_USER
    msg['To'] = GMAIL_USER
    msg['Subject'] = f'NSE Daily - {datetime.now(ist).strftime("%d/%m/%Y")} ({total})'
    msg.attach(MIMEText(body, 'html'))
    
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(GMAIL_USER, GMAIL_PASS)
            server.send_message(msg)
        print(f"✅ EMAIL SENT! {total} announcements")
        return True
    except Exception as e:
        print(f"❌ Email error: {e}")
        return False

if __name__ == "__main__":
    print("🤖 NSE Agent starting...")
    announcements = scrape_nse()
    
    if announcements:
        print(f"📧 Sending email with {len(announcements)} announcements...")
        send_email(announcements)
        print("🎉 Complete!")
    else:
        print("⚠️ No announcements found")
        send_email([])
