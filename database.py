import psycopg2
from psycopg2.extras import RealDictCursor

# Dirección oficial IPv4 Session Pooler de tu proyecto en Supabase:
DATABASE_URL = "postgresql://postgres.tmgyhsycmxmmkfalqorl:Groenlandia27..@aws-1-us-east-1.pooler.supabase.com:5432/postgres?sslmode=require"

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn