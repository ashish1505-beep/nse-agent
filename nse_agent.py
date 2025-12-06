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
GMAIL_USER = os.getenv('GMAIL_USER')
GMAIL_PASS = os.getenv('GMAIL_PASS')

def scrape_nse():
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
    headers = {
        'Authorization': f'Bearer {GROK_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    prompt = f"EQUITY RESEARCH SUMMARY (2-3 bullets, 40 words):\n{context}\n\n{text[:500]}\n\nKey decision + investment impact:"
    
    data = {
        "model": "grok-beta",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 100,
        "temperature": 0.1
    }
    
    try:
        response = requests.post('https://api.x.ai/v1/chat/completions', headers=headers, json=data)
        return response.json()['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"Grok error: {e}")
        return "Summary unavailable"

def summarize_all_announcements(df):
    summaries = []
    
    for idx, row in df.iterrows():
        print(f"🤖 Summarizing {row['SYMBOL']} - {row['SUBJECT']}")
        
        context = f"{row['SYMBOL']} ({row['COMPANY NAME']}) - {row['SUBJECT']}"
        summary = grok_summarize(str(row['DETAILS']), context)
        
        summaries.append({
            'SYMBOL': row['SYMBOL'],
            'COMPANY': row['COMPANY NAME'],
            'SUBJECT': row['SUBJECT'],
            'AI_SUMMARY': summary,
            'TIME': row['BROADCAST DATE/TIME']
        })
        
        sleep(0.3)
    
    return pd.DataFrame(summaries)

def create_email_table(df):
    html_rows = []
    
    for _, row in df.iterrows():
        html_rows.append(f"""<tr style="border-bottom: 1px solid #e5e7eb;">
            <td style="padding: 12px; font-weight: bold; color: #1f2937;">
                <strong>{row['SYMBOL']}</strong><br>
                <small style="color: #6b7280;">{row['COMPANY']}</small>
            </td>
            <td style="padding: 12px; font-size: 14px; color: #374151;">
                {row['SUBJECT']}
            </td>
            <td style="padding: 12px; background: #f8fafc; border-radius: 8px; color: #1e40af;">
                {row['AI_SUMMARY']}
            </td>
            <td style="padding: 12px; color: #6b7280; font-size: 12px;">
                {row['TIME']}
            </td>
        </tr>""")
    
    return "".join(html_rows)

def send_complete_email(df):
    total = len(df)
    
    msg = MIMEMultipart()
    msg['From'] = GMAIL_USER
    msg['To'] = GMAIL_USER
    msg['Subject'] = f'NSE Daily Digest - {datetime.now(ist).strftime("%d/%m/%Y")} ({total} announcements)'
    
    if df.empty:
        body = "<h1>No new announcements</h1>"
    else:
        table_rows = create_email_table(df)
        
        body = f"""<html><body style="font-family: Arial, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%); color: white; padding: 30px; border-radius: 20px; margin-bottom: 30px; text-align: center;">
                <h1 style="margin: 0; font-size: 28px;">NSE Daily Digest</h1>
                <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">
                    {datetime.now(ist).strftime("%d/%m/%Y %H:%M")} IST | {total} announcements analyzed
                </p>
            </div>
            
            <div style="background: white; border-radius: 15px; overflow: hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.1);">
                <table style="width: 100%; border-collapse: collapse;">
                    <thead>
                        <tr style="background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%); color: white;">
                            <th style="padding: 15px; text-align: left;">STOCK</th>
                            <th style="padding: 15px; text-align: left;">SUBJECT</th>
                            <th style="padding: 15px; text-align: left;">AI SUMMARY</th>
                            <th style="padding: 15px; text-align: left;">TIME</th>
                        </tr>
                    </thead>
                    <tbody>
                        {table_rows}
                    </tbody>
                </table>
            </div>
            
            <div style="text-align: center; margin-top: 30px; padding: 20px; background: #f3f4f6; border-radius: 12px;">
                <p style="color: #6b7280; margin: 0;">Watchlist: RELIANCE, KPITTECH, JTLIND, MOTILALOFS | Daily 9:30 AM IST</p>
            </div>
        </body></html>"""
    
    msg.attach(MIMEText(body, 'html'))
    
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(GMAIL_USER, GMAIL_PASS)
            server.send_message(msg)
        print(f"✅ EMAIL SENT! {total} announcements summarized.")
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False

if __name__ == "__main__":
    print("🤖 NSE AI Agent starting...")
    
    print("📊 Scraping NSE...")
    df_raw = scrape_nse()
    
    if df_raw.empty:
        print("No new announcements")
        send_complete_email(pd.DataFrame())
    else:
        print(f"Found {len(df_raw)} announcements")
        
        print("🧠 AI analyzing...")
        df_summaries = summarize_all_announcements(df_raw)
        
        print("📧 Sending email...")
        send_complete_email(df_summaries)
        
        print("🎉 Complete!")
