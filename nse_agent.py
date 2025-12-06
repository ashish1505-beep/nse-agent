import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import pytz
import requests
import os
from time import sleep

ist = pytz.timezone('Asia/Kolkata')
GROK_API_KEY = os.getenv('GROK_API_KEY')
GMAIL_USER = os.getenv('GMAIL_USER')
GMAIL_PASS = os.getenv('GMAIL_PASS')

def scrape_nse():
    print("📊 Fetching NSE data...")
    try:
        # Direct API approach - simpler than scraping
        url = "https://www.nseindia.com/api/corporate-filings-announcements"
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Parse announcements
            announcements = []
            if 'announcements' in data:
                for item in data['announcements'][:50]:
                    announcements.append({
                        'SYMBOL': item.get('symbol', 'N/A'),
                        'COMPANY': item.get('company_name', 'N/A'),
                        'SUBJECT': item.get('subject', 'N/A'),
                        'DETAILS': item.get('details', 'N/A'),
                        'TIME': item.get('broadcast_time', 'N/A')
                    })
            
            return announcements
        else:
            print(f"API error: {response.status_code}")
            return []
    except Exception as e:
        print(f"Scrape error: {e}")
        return []

def grok_summarize(text, context=""):
    headers = {
        'Authorization': f'Bearer {GROK_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    prompt = f"EQUITY RESEARCH (2 bullets, 40 words): {context}\n{text[:400]}"
    
    data = {
        "model": "grok-beta",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 80,
        "temperature": 0.1
    }
    
    try:
        response = requests.post('https://api.x.ai/v1/chat/completions', headers=headers, json=data, timeout=15)
        return response.json()['choices'][0]['message']['content'].strip()
    except:
        return "Key announcement"

def send_email(announcements):
    total = len(announcements)
    
    if total == 0:
        body = "<h1>No new announcements</h1>"
    else:
        rows = ""
        for item in announcements[:20]:
            summary = grok_summarize(item['DETAILS'], f"{item['SYMBOL']} - {item['SUBJECT']}")
            rows += f"""<tr style="border-bottom: 1px solid #ddd;">
                <td style="padding: 10px; font-weight: bold;">{item['SYMBOL']}</td>
                <td style="padding: 10px;">{item['SUBJECT']}</td>
                <td style="padding: 10px;">{summary}</td>
                <td style="padding: 10px; font-size: 12px;">{item['TIME']}</td>
            </tr>"""
            sleep(0.2)
        
        body = f"""<html><body style="font-family: Arial; max-width: 900px;">
            <h1>NSE Daily Digest - {datetime.now(ist).strftime("%d/%m/%Y")}</h1>
            <p>{total} announcements analyzed</p>
            <table style="width: 100%; border-collapse: collapse;">
                <tr style="background: #1e40af; color: white;">
                    <th style="padding: 10px;">STOCK</th>
                    <th style="padding: 10px;">SUBJECT</th>
                    <th style="padding: 10px;">AI SUMMARY</th>
                    <th style="padding: 10px;">TIME</th>
                </tr>
                {rows}
            </table>
        </body></html>"""
    
    msg = MIMEMultipart()
    msg['From'] = GMAIL_USER
    msg['To'] = GMAIL_USER
    msg['Subject'] = f'NSE Daily - {datetime.now(ist).strftime("%d/%m/%Y")}'
    msg.attach(MIMEText(body, 'html'))
    
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(GMAIL_USER, GMAIL_PASS)
            server.send_message(msg)
        print(f"✅ EMAIL SENT! {total} announcements")
    except Exception as e:
        print(f"Email error: {e}")

if __name__ == "__main__":
    print("🤖 NSE Agent starting...")
    announcements = scrape_nse()
    
    if announcements:
        send_email(announcements)
    else:
        print("No data found")
