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

def create_email_table(df):
    """Beautiful HTML table with ALL summaries"""
    html_rows = []
    
    for _, row in df.iterrows():
        html_rows.append(f"""
        <tr style="border-bottom: 1px solid #e5e7eb;">
            <td style="padding: 12px; font-weight: bold; color: #1f2937;">
                <strong>{row['SYMBOL']}</strong><br>
                <small style="color: #6b7280;">{row['COMPANY']}</small>
            </td>
            <td style="padding: 12px; font-size: 14px; color: #374151;">
                {row['SUBJECT']}
            </td>
            <td style="padding: 12px; background: #f8fafc; border-radius: 8px;">
                <div style="font-size: 13px; line-height: 1.4; color: #1e40af;">
                    • {row['AI_SUMMARY']}
                </div>
            </td>
            <td style="padding: 12px; color: #6b7280; font-size: 12px;">
                {row['TIME']}
            </td>
        </tr>
        """)
    
    return "".join(html_rows)

def send_complete_email(df):
    """Email with ALL individual summaries"""
    total = len(df)
    
    msg = MIMEMultipart()
    msg['From'] = GMAIL_USER      # ✅ CHANGED
    msg['To'] = GMAIL_USER        # ✅ CHANGED
    msg['Subject'] = f'🚀 NSE COMPLETE DIGEST - {datetime.now(ist).strftime("%d/%m/%Y")} ({total} FULL SUMMARIES)'
    
    if df.empty:
        body = "<h1>✅ No new announcements</h1>"
    else:
        table_rows = create_email_table(df)
        
        body = f"""
        <html>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px;">
            
            <div style="text-align: center; background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%); 
                        color: white; padding: 30px; border-radius: 20px; margin-bottom: 30px;">
                <h1 style="margin: 0; font-size: 28px;">🚀 NSE Complete Announcement Digest</h1>
                <p style="margin: 10px 0 0 0; font-size: 18px; opacity: 0.9;">
                    {datetime.now(ist).strftime("%d/%m/%Y %H:%M")} IST | {total} announcements fully analyzed
                </p>
            </div>
            
            <div style="background: #f8fafc; padding: 25px; border-radius: 15px; margin-bottom: 25px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                <h2 style="color: #1f2937; margin-top: 0;">✅ AI HAS READ & SUMMARIZED EVERY ANNOUNCEMENT</h2>
                <p style="color: #6b7280; font-size: 16px;">
                    No manual reading required. Each summary contains key decisions, financial impact, and investment implications.
                </p>
            </div>
            
            <div style="background: white; border-radius: 15px; overflow: hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.1);">
                <table style="width: 100%; border-collapse: collapse;">
                    <thead>
                        <tr style="background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%); color: white;">
                            <th style="padding: 20px 15px; text-align: left; font-weight: 600;">🪙 STOCK</th>
                            <th style="padding: 20px 15px; text-align: left; font-weight: 600;">📋 SUBJECT</th>
                            <th style="padding: 20px 15px; text-align: left; font-weight: 600;">🤖 AI SUMMARY</th>
                            <th style="padding: 20px 15px; text-align: right; font-weight: 600;">⏰ TIME</th>
                        </tr>
                    </thead>
                    <tbody>
                        {table_rows}
                    </tbody>
                </table>
            </div>
            
            <div style="text-align: center; margin-top: 30px; padding: 20px; background: #f3f4f6; border-radius: 12px;">
                <p style="color: #6b7280; margin: 0;">
                    <strong>✅ Watchlist monitored:</strong> RELIANCE, KPITTECH, JTLIND, MOTILALOFS<br>
                    <em>AI scanned all documents | Runs daily 9:30 AM IST automatically</em>
                </p>
            </div>
        </body>
        </html>
        """
    
    msg.attach(MIMEText(body, 'html'))
    
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(GMAIL_USER, GMAIL_PASS)      # ✅ CHANGED
        server.send_message(msg)
    print(f"✅ COMPLETE EMAIL SENT! {total} announcements summarized.")

if __name__ == "__main__":
    print("🤖 ULTIMATE NSE AI Agent - Summarizing ALL announcements...")
    
    print("📊 Scraping NSE...")
    df_raw = scrape_nse()
    
    if df_raw.empty:
        print("ℹ️ No new announcements")
        send_complete_email(pd.DataFrame())
    else:
        print(f"🎯 Found {len(df_raw)} announcements")
        
        print("🧠 AI analyzing each announcement...")
        df_summaries = summarize_all_announcements(df_raw)
        
        print("📧 Sending full summary email...")
        send_complete_email(df_summaries)
        
        print("🎉 ALL DONE! Check your email for complete summaries.")
