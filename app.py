from flask import Flask, request, jsonify, session, send_file
from flask_cors import CORS
import mysql.connector
from mysql.connector import pooling
import requests
import os
import bcrypt
import re
import jwt
import datetime
from functools import wraps
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
# Be more specific with CORS in production for security
CORS(app, supports_credentials=True)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'fallback-secret-key-change-in-production')
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False

# Database configuration
db_config = {
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'flashcard_db')
}

# Create a connection pool
try:
    db_pool = mysql.connector.pooling.MySQLConnectionPool(
        pool_name="db_pool",
        pool_size=5,
        **db_config
    )
    print("Database connection pool created successfully!")
except mysql.connector.Error as e:
    print(f"Error creating connection pool: {e}")
    db_pool = None

def get_db_connection():
    if db_pool:
        return db_pool.get_connection()
    return mysql.connector.connect(**db_config)

# JWT Configuration
JWT_SECRET = os.getenv('JWT_SECRET', 'fallback-jwt-secret')
JWT_ALGORITHM = 'HS256'

# Hugging Face API Configuration
HF_TOKEN = os.getenv('HUGGING_FACE_TOKEN')
if not HF_TOKEN:
    raise ValueError("HUGGING_FACE_TOKEN environment variable not set.")
    
# Using a more reliable model
HF_API_URL = "https://api-inference.huggingface.co/models/google/flan-t5-base"
HF_HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"} if HF_TOKEN else {}

# Early adopter and premium tier constants
EARLY_ADOPTER_LIMIT = 5
PREMIUM_TIER = 'premium'

# IntaSend Configuration
try:
    from intasend import APIService
    
    INTASEND_PUBLISHABLE_KEY = os.getenv('INTASEND_PUBLISHABLE_KEY')
    INTASEND_SECRET_KEY = os.getenv('INTASEND_SECRET_KEY')
    
    # Validate Intasend keys
    if INTASEND_PUBLISHABLE_KEY and INTASEND_SECRET_KEY:
        # Initialize Intasend service (SANDBOX MODE - test=True)
        intasend_service = APIService(
            publishable_key=INTASEND_PUBLISHABLE_KEY,
            token=INTASEND_SECRET_KEY,
            test=True
        )
        print("IntaSend payment service initialized!")
    else:
        print("Warning: Intasend keys not set. Payment features will be disabled.")
        intasend_service = None
        print("IntaSend keys not set. Payment features disabled.")
except ImportError:
    print("Warning: intasend package not installed. Payment features disabled.")
    intasend_service = None

# --- PASSWORD UTILITY FUNCTIONS ---
def hash_password(password):
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(stored_password, provided_password):
    """Verify a stored password against one provided by user"""
    return bcrypt.checkpw(
        provided_password.encode('utf-8'),
        stored_password.encode('utf-8')
    )

def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def is_valid_username(username):
    """Basic username validation"""
    return 3 <= len(username) <= 20 and username.isalnum()

# --- DATABASE INITIALIZATION ---
def initialize_default_deck():
    """Ensure a default deck and user exist in the database."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if default user exists, create if not
        cursor.execute("SELECT id FROM users WHERE id = 1")
        user_result = cursor.fetchone()
        
        if not user_result:
            # Create a default user with hashed password
            hashed_password = hash_password('demo123')
            cursor.execute(
                "INSERT INTO users (id, username, email, password_hash, is_premium) VALUES (%s, %s, %s, %s, %s)",
                (1, 'demo_user', 'demo@example.com', hashed_password, False)
            )
            print("Default user created successfully!")
        
        # Check if default deck already exists
        cursor.execute("SELECT id FROM decks WHERE id = 1")
        deck_result = cursor.fetchone()
        
        if not deck_result:
            # Create a default deck if it doesn't exist
            cursor.execute(
                "INSERT INTO decks (id, user_id, title, description) VALUES (%s, %s, %s, %s)",
                (1, 1, 'Default Deck', 'Automatically created default deck for flashcards')
            )
            conn.commit()
            print("Default deck created successfully!")
        else:
            print("Default deck already exists.")
            
    except mysql.connector.Error as e:
        print(f"Error initializing default deck: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

# Initialize the default deck when the app starts
initialize_default_deck()

# --- UTILITY FUNCTIONS ---
def clean_text(text):
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s.,!?;:]', '', text)
    return text.strip()

def split_into_sentences(text):
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s for s in sentences if s and len(s.split()) > 3]

def generate_question(context):
    try:
        if not HF_TOKEN:
            raise Exception("Hugging Face token not configured")
            
        response = requests.post(
            HF_API_URL,
            headers=HF_HEADERS, 
            json={"inputs": f"Generate a question about: {context}"}, 
            timeout=15
        )
        response.raise_for_status()
        result = response.json()
        
        if result and isinstance(result, list) and 'generated_text' in result[0]:
            return result[0]['generated_text']
        elif isinstance(result, dict) and 'generated_text' in result:
            return result['generated_text']
            
    except Exception as e:
        print(f"Hugging Face API error: {e}")
    
    # Fallback
    words = context.split()
    if len(words) > 3:
        blank_index = len(words) // 2
        words[blank_index] = "______"
        return " ".join(words)
    return f"What is {context}?"

def store_flashcards(flashcards, user_id):
    if not flashcards:
        return

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        for card in flashcards:
            cursor.execute(
                "INSERT INTO flashcards (user_id, question, answer) VALUES (%s, %s, %s)",
                (user_id, card['question'], card['answer'])
            )
        
        conn.commit()
        print(f"Stored {len(flashcards)} flashcards for user {user_id}")
        
    except mysql.connector.Error as e:
        print(f"Database error: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

# JWT Token Decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
            
        try:
            if token.startswith('Bearer '):
                token = token[7:]
                
            data = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT id, username, email, is_premium FROM users WHERE id = %s", (data['user_id'],))
            current_user = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if not current_user:
                return jsonify({'error': 'User not found'}), 401
                
            request.current_user = current_user
            
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token is invalid'}), 401
            
        return f(*args, **kwargs)
        
    return decorated

# Initialize Database
def initialize_database():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                is_premium BOOLEAN DEFAULT FALSE,
                tier ENUM('free', 'early_adopter', 'premium') DEFAULT 'free',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create flashcards table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS flashcards (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # Create payments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                invoice_id VARCHAR(255) NOT NULL,
                amount DECIMAL(10, 2) NOT NULL,
                currency VARCHAR(10) NOT NULL,
                status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        conn.commit()
        print("Database tables initialized successfully!")
        
    except mysql.connector.Error as e:
        print(f"Error initializing database: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

# Initialize the database when the app starts
initialize_database()

# Route to serve HTML files
@app.route('/')
def serve_index():
    return send_file('index.html')

@app.route('/ai-app')
def serve_ai_app():
    return send_file('ai-app.html')

# Authentication endpoints
@app.route('/register', methods=['POST'])
def register():
    conn = None
    try:
        data = request.json
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        # Validation
        if not all([username, email, password]):
            return jsonify({'error': 'All fields are required'}), 400
            
        if not is_valid_username(username):
            return jsonify({'error': 'Username must be 3-20 alphanumeric characters'}), 400
            
        if not is_valid_email(email):
            return jsonify({'error': 'Invalid email format'}), 400
            
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        
        # Check if user already exists
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM users WHERE username = %s OR email = %s", 
                      (username, email))
        if cursor.fetchone():
            return jsonify({'error': 'Username or email already exists'}), 400
        
        # Check early adopter status
        cursor.execute("SELECT COUNT(*) as count FROM users WHERE tier = 'early_adopter'")
        early_adopter_count = cursor.fetchone()[0]
        tier = 'early_adopter' if early_adopter_count < EARLY_ADOPTER_LIMIT else 'free'
        
        # Create new user
        hashed_password = hash_password(password)
        cursor.execute(
            "INSERT INTO users (username, email, password_hash, is_premium) VALUES (%s, %s, %s, %s)",
            (username, email, hashed_password, False)
        )
        conn.commit()
        
        user_id = cursor.lastrowid
        
        # Start user session
        session['user_id'] = user_id
        session['username'] = username
        
        return jsonify({
            'message': 'Registration successful',
            'user': {'id': user_id, 'username': username}
        })
        
    except mysql.connector.Error as e:
        print(f"Database error during registration: {e}")
        return jsonify({'error': 'Database error'}), 500
    except Exception as e:
        print(f"Registration failed: {e}")
        return jsonify({'error': 'Registration failed'}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/login', methods=['POST'])
def login():
    """Login an existing user"""
    conn = None
    try:
        data = request.json
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400
        
        # Find user in database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, password_hash, is_premium FROM users WHERE username = %s",
            (username,)
        )
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401
            
        user_id, username, stored_password, tier = user
        if not verify_password(stored_password, password):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Generate JWT token
        token = jwt.encode({
            'user_id': user_id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }, JWT_SECRET, algorithm=JWT_ALGORITHM)
        
        return jsonify({
            'success': 'Login successful',
            'token': token,
            'user': {
                'id': user_id,
                'username': username,
                'tier': tier
            }
        })
        
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({'error': 'Login failed'}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/verify-token', methods=['POST'])
def verify_token():
    try:
        data = request.json
        token = data.get('token', '')
        
        if not token:
            return jsonify({'error': 'Token is required'}), 400
            
        if token.startswith('Bearer '):
            token = token[7:]
            
        # Decode and verify token
        token_data = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        
        # Verify user exists
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, username, email, tier FROM users WHERE id = %s", (token_data['user_id'],))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user:
            return jsonify({
                'authenticated': True,
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'email': user['email'],
                    'tier': user['tier']
                }
            })
        else:
            return jsonify({'authenticated': False}), 401
            
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token has expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Token is invalid'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Payment endpoints
@app.route('/create-payment-intent', methods=['POST'])
@token_required
def create_payment_intent():
    try:
        if not intasend_service:
            return jsonify({'error': 'Payment service not configured'}), 503
            
        amount = 1  # $1
        currency = 'USD'
        
        payment = intasend_service.create_payment(
            amount=amount,
            currency=currency,
            methods=['CARD', 'MPESA', 'BANK'],
            first_name=request.current_user['username'],
            email=request.current_user['email'],
            narrative='BrainFlip Premium Access'
        )
        
        # Store payment in database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO payments (user_id, invoice_id, amount, currency) VALUES (%s, %s, %s, %s)",
            (request.current_user['id'], payment['invoice']['invoice_id'], amount, currency)
        )
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'invoice_id': payment['invoice']['invoice_id'],
            'payment_url': payment['invoice']['url'],
            'amount': amount,
            'currency': currency
        })
    
    except Exception as e:
        print(f"Payment error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/verify-payment', methods=['POST'])
@token_required
def verify_payment():
    try:
        data = request.json
        invoice_id = data.get('invoice_id', '')
        
        if not invoice_id:
            return jsonify({'error': 'Invoice ID is required'}), 400
        
        if not intasend_service:
            return jsonify({'error': 'Payment service not configured'}), 503
            
        # Check payment status with IntaSend
        status = intasend_service.status(invoice_id)
        
        if status['invoice']['state'] == 'COMPLETE':
            # Update payment status in database
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "UPDATE payments SET status = 'COMPLETED' WHERE invoice_id = %s",
                (invoice_id,)
            )
            
            # Upgrade user to premium
            cursor.execute(
                "UPDATE users SET tier = %s WHERE id = %s",
                (PREMIUM_TIER, request.current_user['id'])
            )
            
            conn.commit()
            cursor.close()
            conn.close()
            
            # Generate new token with updated user info
            new_token = jwt.encode({
                'user_id': request.current_user['id'],
                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
            }, JWT_SECRET, algorithm=JWT_ALGORITHM)
            
            return jsonify({
                'success': 'Payment verified and account upgraded to premium',
                'token': new_token,
                'tier': PREMIUM_TIER
            })
        else:
            return jsonify({
                'error': 'Payment not completed',
                'status': status['invoice']['state']
            }), 400
    
    except Exception as e:
        print(f"Payment verification error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/payment-webhook', methods=['POST'])
def payment_webhook():
    """Handle IntaSend payment webhooks"""
    try:
        if not intasend_service:
            return jsonify({'error': 'Payment service not configured'}), 503
            
        # Verify webhook signature (important for security)
        signature = request.headers.get('X-IntaSend-Signature')
        payload = request.get_data()
        
        # Verify signature using your secret token
        # Implementation depends on IntaSend's webhook signature method
        
        data = request.json
        invoice_id = data.get('invoice_id')
        status = data.get('status')
        
        # Update payment status in database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE payments SET status = %s WHERE invoice_id = %s",
            (status, invoice_id)
        )
        
        # If payment is complete, upgrade user
        if status == 'COMPLETE':
            cursor.execute(
                "SELECT user_id FROM payments WHERE invoice_id = %s",
                (invoice_id,)
            )
            result = cursor.fetchone()
            
            if result:
                user_id = result[0]
                cursor.execute(
                    "UPDATE users SET tier = %s WHERE id = %s",
                    (PREMIUM_TIER, user_id)
                )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True})
    
    except Exception as e:
        print(f"Webhook error: {e}")
        return jsonify({'error': str(e)}), 500

# Flashcard endpoints
@app.route('/generate-flashcards', methods=['POST'])
@token_required
def generate_flashcards_route():
    try:
        data = request.json
        notes = data.get('notes', '')
        
        if not notes:
            return jsonify({'error': 'No notes provided'}), 400
        
        # Check if user has access
        if request.current_user['tier'] == 'free':
            return jsonify({
                'error': 'Premium feature. Upgrade to access AI flashcard generation.',
                'requiresPayment': True
            }), 402
        
        cleaned_notes = clean_text(notes)
        sentences = split_into_sentences(cleaned_notes)
        
        flashcards = []
        for sentence in sentences[:10]:
            question = generate_question(sentence)
            if question:
                flashcards.append({'question': question, 'answer': sentence})
        
        if not flashcards:
            return jsonify({'error': 'Could not generate flashcards from the provided text.'}), 400
            
        # Store in the database
        store_flashcards(flashcards, request.current_user['id'])
        
        return jsonify({
            'flashcards': flashcards,
            'tier': request.current_user['tier']
        })
        
    except Exception as e:
        print(f"Flashcard generation error: {e}")
        return jsonify({'error': 'An internal server error occurred.'}), 500

@app.route('/flashcards', methods=['GET'])
@token_required
def get_flashcards():
    """Get all flashcards for the current user"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute(
            "SELECT question, answer FROM flashcards WHERE user_id = %s ORDER BY created_at DESC",
            (request.current_user['id'],)
        )
        flashcards = cursor.fetchall()
        
        return jsonify({'flashcards': flashcards})
        
    except mysql.connector.Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'service': 'BrainFlip API'})

if __name__ == '__main__':
    # This will fail if FLASK_SECRET_KEY is not set in .env
    if not app.secret_key:
        raise ValueError("FLASK_SECRET_KEY is not set. Please set it in your .env file.")
    app.run(debug=True, port=5000)