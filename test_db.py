from dotenv import load_dotenv
load_dotenv()

import os
import psycopg2

url = os.environ.get('DATABASE_URL')
if not url:
    print("ERROR: DATABASE_URL not found in .env")
    exit(1)

print(f"Connecting to: {url[:50]}...")
try:
    conn = psycopg2.connect(url, sslmode='require')
    cur = conn.cursor()
    cur.execute('SELECT version();')
    print("Connected!", cur.fetchone()[0])
    conn.close()
    print("All good - Supabase connection works.")
except Exception as e:
    print("Connection failed:", e)
