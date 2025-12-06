# 🚀 ULTIMATE: AI Summarizes EVERY SINGLE Announcement
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import pytz
import requests
from bs4 import BeautifulSoup
import os
from time import sleep

ist = pytz.timezone('Asia/Kolkata')
GROK_API_KEY = os.getenv('GROK_API_KEY')
GMAIL_USER = os.getenv('GMAIL_USER')      # ✅ CHANGED
GMAIL_PASS = os.getenv('GMAIL_PASS')      # ✅ CHANGED

def scrape_nse():
    """Scrape ALL NSE announcements from last 24h"""
    url = "https://www.nseindia.com/companies-listing/corporate-filings-announcements"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    tables = soup.find_all('table')
    if tables:
        df = pd.read_html(str(tables[0]))[0]
        df['parsed_time'] = pd.to_datetime(df['BROADCAST DATE/TIME'], format='%d-%b-%Y %H:%M:%S', errors='coerce')
        
        now = datetime.now(ist)
        yesterday = now - timedelta(hours=24)
        recent = df[df['parsed_time'] >= yesterday].copy()
        
        recent = recent.dropna(subset=['SYMBOL', 'SUBJECT'])
        return recent.head(50)
    return pd.DataFrame()

def grok_summarize(text, context=""):
    """AI summarizes single announcement"""
    headers = {
        'Authorization': f'Bearer {GROK_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    prompt = f"""
    EQUITY RESEARCH SUMMARY (3 bullets max, 50 words total):
    Company: {context}
    
    {text}
    
    Extract: Key decision, financial impact, investment implication.
    """
    
    data = {
        "model": "grok-beta",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 150,
        "temperature": 0.1
    }
    
    try:
        response = requests.post('https://api.x.ai/v1/chat/completions', headers=headers, json=data)
        return response.json()['choices'][0]['message']['content'].strip()
    except:
        return "Summary unavailable"

def summarize_all_announcements(df):
    """AI summarizes EVERY announcement individually"""
    summaries = []
    
    for idx, row in df.iterrows():
        print(f"🤖 Summarizing {row['SYMBOL']} - {row['SUBJECT']}")
        
        context = f"{row['SYMBOL']} ({row['COMPANY NAME']}) - {row['SUBJECT']}"
        summary = grok_summarize(row['DETAILS'], context)
        
        summaries.append({
            'SYMBOL': row['SYMBOL'],
            'COMPANY': row['COMPANY NAME'],
            'SUBJECT': row['SUBJECT'],
            'AI_SUMMARY': summary,
            'TIME': row['BROADCAST DATE/TIME']
        })
        
        sleep(0.5)
    
    return pd.DataFrame(summaries)

def create
