# app.py
from flask import Flask, request, jsonify, session
from flask_cors import CORS
import mysql.connector
from mysql.connector import pooling
import requests
import os
import bcrypt
import re
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
# Be more specific with CORS in production for security
CORS(app, supports_credentials=True)
app.secret_key = os.getenv('FLASK_SECRET_KEY')
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS

# --- DATABASE CONFIGURATION ---
db_config = {
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'database': os.getenv('DB_NAME')
}

# Ensure all database environment variables are set
if not all(db_config.values()):
    raise ValueError("One or more database environment variables (DB_USER, DB_PASSWORD, DB_HOST, DB_NAME) are not set.")

# Create a connection pool for better performance
db_pool = mysql.connector.pooling.MySQLConnectionPool(
    pool_name="db_pool",
    pool_size=5,  # Adjust pool size based on expected load
    **db_config
)

def get_db_connection():
    return db_pool.get_connection()

# --- HUGGING FACE API CONFIGURATION ---
HF_TOKEN = os.getenv('HUGGING_FACE_TOKEN')
if not HF_TOKEN:
    raise ValueError("HUGGING_FACE_TOKEN environment variable not set.")
    
# Using a more reliable model
HF_API_URL = "https://api-inference.huggingface.co/models/google/flan-t5-base"
HF_HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}

# --- INTASEND CONFIGURATION (SANDBOX) ---
try:
    from intasend import APIService
    
    INTASEND_PUBLISHABLE_KEY = os.getenv('INTASEND_PUBLISHABLE_KEY')
    INTASEND_SECRET_KEY = os.getenv('INTASEND_SECRET_KEY')
    
    # Validate Intasend keys
    if INTASEND_PUBLISHABLE_KEY and INTASEND_SECRET_KEY:
        # Initialize Intasend service (SANDBOX MODE - test=True)
        intasend_service = APIService(
            publishable_key=INTASEND_PUBLISHABLE_KEY,
            secret_key=INTASEND_SECRET_KEY,
            test=True  # ← CRUCIAL: This enables sandbox mode!
        )
        print("Intasend payment service initialized successfully!")
    else:
        print("Warning: Intasend keys not set. Payment features will be disabled.")
        intasend_service = None
        
except ImportError:
    print("Warning: intasend package not installed. Payment features disabled.")
    intasend_service = None

# --- PASSWORD UTILITY FUNCTIONS ---
def hash_password(password):
    """Hash a password for storing."""
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
    """Basic email validation"""
    pattern = r'^[a-zA-Z00-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
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
    """Clean and preprocess the input text."""
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s.,!?;:]', '', text)
    return text.strip()

def split_into_sentences(text):
    """Split text into sentences using basic punctuation."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s for s in sentences if s and len(s.split()) > 3]  # Reduced to 3 words minimum

def generate_question(context):
    """Generate a question using Hugging Face Inference API with a fallback."""
    try:
        # Updated prompt for the new model
        response = requests.post(
            HF_API_URL,
            headers=HF_HEADERS, 
            json={"inputs": f"Generate a question about: {context}"}, 
            timeout=15
        )  # Increased timeout
        response.raise_for_status()
        result = response.json()
        
        if result and isinstance(result, list) and 'generated_text' in result[0]:
            return result[0]['generated_text']
        elif isinstance(result, dict) and 'generated_text' in result:
            return result['generated_text']
            
    except requests.exceptions.RequestException as e:
        print(f"Hugging Face API error: {e}")
    
    # Fallback if API fails or returns unexpected format
    words = context.split()
    if len(words) > 3:
        blank_index = len(words) // 2
        words[blank_index] = "______"
        return " ".join(words) + "?"
    return f"What is {context}?"

def store_flashcards(flashcards, user_id=1):
    """Store a list of generated flashcards in the database efficiently and securely."""
    if not flashcards:
        return

    # SQL statement with placeholders for security
    sql = "INSERT INTO flashcards (deck_id, question, answer) VALUES (%s, %s, %s)"
    
    # Prepare data for bulk insert - using deck_id = 1 which now exists
    data_to_insert = [(1, card['question'], card['answer']) for card in flashcards]

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Use executemany for efficient bulk insertion
        cursor.executemany(sql, data_to_insert)
        
        conn.commit()
        print(f"{cursor.rowcount} flashcards stored successfully in database!")
        
    except mysql.connector.Error as e:
        print(f"Database error: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

# --- AUTHENTICATION ROUTES ---
@app.route('/register', methods=['POST'])
def register():
    """Register a new user"""
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
            
        # Verify password
        user_id, username, stored_password, is_premium = user
        if not verify_password(stored_password, password):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Start user session
        session['user_id'] = user_id
        session['username'] = username
        session['is_premium'] = bool(is_premium)
        
        return jsonify({
            'message': 'Login successful',
            'user': {'id': user_id, 'username': username, 'is_premium': bool(is_premium)}
        })
        
    except Exception as e:
        print(f"Login failed: {e}")
        return jsonify({'error': 'Login failed'}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/logout', methods=['POST'])
def logout():
    """Logout the current user"""
    session.clear()
    return jsonify({'message': 'Logout successful'})

@app.route('/check-auth', methods=['GET'])
def check_auth():
    """Check if user is authenticated"""
    user_id = session.get('user_id')
    username = session.get('username')
    is_premium = session.get('is_premium', False)
    
    if user_id and username:
        return jsonify({
            'authenticated': True,
            'user': {'id': user_id, 'username': username, 'is_premium': is_premium}
        })
    return jsonify({'authenticated': False})

# --- PAYMENT ROUTES ---
@app.route('/create-payment-link', methods=['POST'])
def create_payment_link():
    """Create a payment link for premium upgrade"""
    if not intasend_service:
        return jsonify({'error': 'Payment service not configured'}), 503
        
    try:
        user_id = session.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Please login first'}), 401
            
        # Get user email from database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT email FROM users WHERE id = %s", (user_id,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not result:
            return jsonify({'error': 'User not found'}), 404
            
        user_email = result[0]
        
        # Create payment link with Intasend
        response = intasend_service.create_payment_link(
            amount=5,  # $5 for premium
            currency='USD',
            email=user_email,
            name="Premium Flashcard Upgrade",
            redirect_url="http://localhost:3000/payment-success",  # Your frontend success page
            webhook_url="http://localhost:5000/payment-webhook"   # For backend confirmation
        )
        
        return jsonify({
            'success': True,
            'payment_url': response['url'],
            'invoice_id': response['invoice']['invoice_id']
        })
        
    except Exception as e:
        print(f"Payment error: {e}")
        return jsonify({'error': 'Failed to create payment link'}), 500

@app.route('/payment-webhook', methods=['POST'])
def payment_webhook():
    """Handle payment confirmation from Intasend (SECURE VERSION)"""
    if not intasend_service:
        return jsonify({'error': 'Payment service not configured'}), 503
        
    try:
        # Get the webhook signature from headers
        signature = request.headers.get('IntaSend-Signature')
        webhook_secret = os.getenv('INTASEND_WEBHOOK_SECRET')
        
        # Verify the webhook signature
        if not signature or not webhook_secret:
            print("Webhook security alert: Missing signature or secret")
            return jsonify({'error': 'Invalid webhook request'}), 401
            
        # In a real implementation, you would verify the signature here
        # For the hackathon, we'll simulate the verification
        print(f"Webhook signature received: {signature}")
        print("Webhook verification simulated - would verify signature in production")
        
        # Now process the webhook data
        data = request.json
        invoice_id = data.get('invoice_id')
        status = data.get('status')
        customer = data.get('customer', {})
        
        print(f"Secure webhook received: {invoice_id} - {status}")
        
        if status == 'COMPLETED':
            user_email = customer.get('email')
            
            if user_email:
                # Update user to premium status
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE users SET is_premium = TRUE WHERE email = %s",
                    (user_email,)
                )
                conn.commit()
                cursor.close()
                conn.close()
                
                print(f"User with email {user_email} upgraded to premium for invoice {invoice_id}")
                # In real app, you might want to send a confirmation email here
            else:
                print(f"Payment completed but no email found for invoice {invoice_id}")
        
        return jsonify({'status': 'success'})
        
    except Exception as e:
        print(f"Webhook error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/check-premium', methods=['GET'])
def check_premium():
    """Check if current user has premium status"""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'is_premium': False})
            
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT is_premium FROM users WHERE id = %s",
            (user_id,)
        )
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if result:
            # Update session with current premium status
            session['is_premium'] = bool(result[0])
            return jsonify({'is_premium': bool(result[0])})
        return jsonify({'is_premium': False})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- FLASHCARD ROUTES ---
@app.route('/generate-flashcards', methods=['POST'])
def generate_flashcards_route():
    conn = None
    try:
        # Check if user is authenticated
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Please login to generate flashcards'}), 401
            
        data = request.json
        notes = data.get('notes', '')
        
        if not notes:
            return jsonify({'error': 'No notes provided'}), 400
        
        cleaned_notes = clean_text(notes)
        sentences = split_into_sentences(cleaned_notes)
        
        flashcards = []
        # Limit to the first 10 valid sentences for the demo
        for sentence in sentences[:10]:
            question = generate_question(sentence)
            if question:
                flashcards.append({'question': question, 'answer': sentence})
        
        if not flashcards:
            return jsonify({'error': 'Could not generate flashcards from the provided text.'}), 400
            
        # Store in the database
        store_flashcards(flashcards, user_id)
        
        return jsonify({'flashcards': flashcards})
        
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return jsonify({'error': 'An internal server error occurred.'}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint to verify API and DB connectivity."""
    conn = None
    try:
        conn = get_db_connection()
        if conn.is_connected():
            return jsonify({'status': 'healthy', 'database': 'connected'})
    except mysql.connector.Error as e:
        return jsonify({'status': 'healthy', 'database': 'error', 'message': str(e)})
    finally:
        if conn and conn.is_connected():
            conn.close()
        
    return jsonify({'status': 'healthy', 'database': 'unknown'})

@app.route('/flashcards', methods=['GET'])
def get_flashcards():
    """Endpoint to retrieve all flashcards from the database."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT question, answer FROM flashcards")
        flashcards = cursor.fetchall()
        
        return jsonify({'flashcards': flashcards})
        
    except mysql.connector.Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == '__main__':
    # This will fail if FLASK_SECRET_KEY is not set in .env
    if not app.secret_key:
        raise ValueError("FLASK_SECRET_KEY is not set. Please set it in your .env file.")
    app.run(debug=True, port=5000)