import psycopg2
from psycopg2.extras import RealDictCursor
from config import Config

def get_db_connection():
    conn = psycopg2.connect(
        Config.DATABASE_URL,
        cursor_factory=RealDictCursor
    )
    return conn

def execute_query(query, params=None, fetch=True):
    """Execute a database query"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(query, params)
        
        if fetch:
            result = cursor.fetchall()
            conn.close()
            return result
        else:
            conn.commit()
            conn.close()
            return True
    except Exception as e:
        conn.close()
        raise e