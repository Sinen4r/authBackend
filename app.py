import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
import jwt
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# CORS configuration
if os.environ.get('FLASK_ENV') == 'production':
    CORS(app, origins=[os.environ.get('FRONTEND_URL', '*')])
else:
    CORS(app)

# Secret key for JWT
SECRET_KEY = os.environ.get('SECRET_KEY', 'fsd5f1sd2fsd1c5ds4')

# DB config
def get_db_config():
    return {
        'host': os.environ.get('MYSQL_SERVICE_HOST', 'mysql'),
        'port': int(os.environ.get('MYSQL_SERVICE_PORT', 3306)),
        'database': os.environ.get('MYSQL_DATABASE', 'authdb'),
        'user': os.environ.get('MYSQL_USER', 'userXAB'),
        'password': os.environ.get('MYSQL_PASSWORD', 'WEgItpR7gAmiHNUc')
    }

def get_db_connection():
    config = get_db_config()
    return mysql.connector.connect(
        host=config['host'],
        port=config['port'],
        database=config['database'],
        user=config['user'],
        password=config['password'],
        connection_timeout=10
    )

# -------- Health check --------
@app.route('/api/health', methods=['GET'])
def health_check():
    try:
        conn = get_db_connection()
        cur = conn.cursor(buffered=True)
        cur.execute("SELECT 1")
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

# -------- Signup --------
@app.route('/api/auth/signup', methods=['POST'])
def signup():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'student')

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    try:
        cur.execute(
            "INSERT INTO users (email, password_hash, role) VALUES (%s, %s, %s)",
            (email, hashed_password, role)
        )
        conn.commit()
        user_id = cur.lastrowid
        cur.execute("SELECT id, email, role FROM users WHERE id=%s", (user_id,))
        user = cur.fetchone()
    except mysql.connector.Error as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 409
    finally:
        cur.close()
        conn.close()

    return jsonify(user), 201

# -------- Login --------
@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT id, email, password_hash, role FROM users WHERE email=%s", (email,))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if not user or not check_password_hash(user['password_hash'], password):
        return jsonify({"error": "Invalid credentials"}), 401

    token = jwt.encode(
        {
            "user_id": user["id"],
            "role": user["role"],
            "exp": datetime.utcnow() + timedelta(hours=2)
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

# -------- Run --------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
