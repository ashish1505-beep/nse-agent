# 🚫 DON'T EDIT - Just copy entire code
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import pytz
import requests
from bs4 import BeautifulSoup
import os

ist = pytz.timezone('Asia/Kolkata')
GROK_API_KEY = os.getenv('GROK_API_KEY')
GMAIL_USER = os.getenv('GMAIL_USER')
GMAIL_PASS = os.getenv('GMAIL_PASS')

def scrape_nse():
    url = "https://www.nseindia.com/companies-listing/corporate-filings-announcements"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Extract table data (matches your attachment format)
    tables = soup.find_all('table')
    if tables:
        df = pd.read_html(str(tables[0]))[0]
        
        # Filter last 24 hours (your exact date format)
        df['parsed_time'] = pd.to_datetime(df['BROADCAST DATE/TIME'], format='%d-%b-%Y %H:%M:%S', errors='coerce')
        now = datetime.now(ist)
        yesterday = now - timedelta(hours=24)
        recent = df[df['parsed_time'] >= yesterday]
        return recent
    return pd.DataFrame()

def ai_summary(df):
    if df.empty:
        return "No new announcements"
    
    prompt = f"""
    Analyze NSE announcements for equity research:
    - Total: {len(df)}
    - Watchlist: RELIANCE, KPITTECH, JTLIND, MOTILALOFS
    - Priority: Board Meetings, Results, Allotments
    
    TOP 3 ALERTS + category summary please.
    """
    
    headers = {
        'Authorization': f'Bearer {GROK_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    data = {
        "model": "grok-beta",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 500
    }
    
    response = requests.post('https://api.x.ai/v1/chat/completions', 
                           headers=headers, json=data)
    return response.json()['choices'][0]['message']['content']

def send_email(summary, df):
    msg = MIMEMultipart()
    msg['From'] = GMAIL_USER
    msg['To'] = GMAIL_USER
    msg['Subject'] = f'🚀 NSE Daily Report - {datetime.now(ist).strftime("%d/%m/%Y")}'
    
    if df.empty:
        body = "<h2>No new announcements today</h2>"
    else:
        table = df.groupby(['SUBJECT','SYMBOL']).size().reset_index(name='Count').head(10).to_html()
        body = f"""
        <h2>📊 NSE Announcements ({len(df)} total)</h2>
        <h3>🤖 AI Summary:</h3>
        <div style="background:#e3f2fd; padding:15px; border-radius:10px;">
        <pre style="white-space:pre-wrap; font-size:14px;">{summary}</pre>
        </div>
        <h3>📈 Breakdown:</h3>
        {table}
        """
    
    msg.attach(MIMEText(body, 'html'))
    
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(GMAIL_USER, GMAIL_PASS)
        server.send_message(msg)
    print("✅ Email sent!")

if __name__ == "__main__":
    print("🤖 NSE Agent starting...")
    df = scrape_nse()
    summary = ai_summary(df)
    send_email(summary, df)
    print("🎉 Daily report complete!")
