import os
from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# CORS configuration for OpenShift
if os.environ.get('FLASK_ENV') == 'production':
    CORS(app, origins=[os.environ.get('FRONTEND_URL', '*')])
else:
    CORS(app)

# Database configuration for OpenShift
def get_db_config():
    """Get database configuration from environment variables"""
    return {
        'host': os.environ.get('MYSQL_SERVICE_HOST', 'mysql'),
        'port': int(os.environ.get('MYSQL_SERVICE_PORT', '3306')),
        'database': os.environ.get('MYSQL_DATABASE', 'authdb'),
        'user': os.environ.get('MYSQL_USER', 'userXAB'),
        'password': os.environ.get('MYSQL_PASSWORD', 'WEgItpR7gAmiHNUc')
    }
import mysql.connector
from mysql.connector import Error

def get_db_connection():
    config = get_db_config()
    try:
        conn = mysql.connector.connect(
            host=config['host'],
            port=config['port'],
            database=config['database'],
            user=config['user'],
            password=config['password'],
            connection_timeout=10  # Note: 'connection_timeout' pour MySQL au lieu de 'connect_timeout'
        )
        return conn
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        raise

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint for OpenShift"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT 1')
        cur.close()
        conn.close()
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'service': 'feedback-backend',
            'database': 'connected'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'service': 'feedback-backend',
            'database': 'disconnected',
            'error': str(e)
        }), 503


from psycopg2.extras import RealDictCursor
from werkzeug.security import generate_password_hash

@app.route('/api/auth/signup', methods=['POST'])
def signup():
    data = request.get_json()

    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'student')

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    hashed_password = generate_password_hash(password)

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cur.execute(
            """
            INSERT INTO users (email, password_hash, role)
            VALUES (%s, %s, %s)
            RETURNING id, email, role
            """,
            (email, hashed_password, role)
        )
        user = cur.fetchone()
        conn.commit()
    except Exception:
        conn.rollback()
        return jsonify({"error": "User already exists"}), 409
    finally:
        cur.close()
        conn.close()

    return jsonify(user), 201
from werkzeug.security import check_password_hash
import jwt
import datetime

SECRET_KEY = "fsd5f1sd2fsd1c5ds4"  # move to env var later

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()

    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        "SELECT id, email, password_hash, role FROM users WHERE email = %s",
        (email,)
    )
    user = cur.fetchone()

    cur.close()
    conn.close()

    if not user or not check_password_hash(user['password_hash'], password):
        return jsonify({"error": "Invalid credentials"}), 401

    token = jwt.encode(
        {
            "user_id": user["id"],
            "role": user["role"],
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=2)
        },
        SECRET_KEY,
        algorithm="HS256"
    )

    return jsonify({
        "token": token,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "role": user["role"]
        }
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)