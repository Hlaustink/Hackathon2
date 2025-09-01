## Flashcard AI Generator 🚀
[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A full-stack web application that uses AI to automatically generate flashcards from study notes. Built for the hackathon with a focus on SDG 4 (Quality Education).

## Features Used
- 🤖 AI-Powered: Uses Hugging Face transformers to generate questions from notes
- 🔐 User Authentication: Secure login/registration with password hashing
- 💳 Monetization Ready: Intasend integration for premium features
- 🏗️ Professional Grade: Connection pooling, error handling, and security best practices
-  📱 Responsive Design: Clean UI with flip-card animations

## Tech Stack
### Frontend
- HTML5, CSS3, JavaScript (ES6+)
- Flip card animations
- Responsive design

### Backend
- Python with Flask framework
- MySQL database with connection pooling
- Hugging Face AI API integration
- Intasend payment processing
- bcrypt for password security

### APIs & services
- Hugging Face Inference API
- Intasend Sandbox API
- Custom RESTful API endpoints

## Installation
### Prerequisites
- Python 3.8+
- MySQL 5.7+
- Node.js (for frontend)

### 1. Clone the repo
``` bash
git clone https://github.com/Hlaustink/Hackathon2.git
cd Hackathon2
```
### 2. Database setup 
```
mysql -u root -p < database.sql
```
### 3. Backend setup 
```
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your actual values
```
### 4. Frontend setup
```
# No build process needed - pure HTML/CSS/JS
# Just open index.html in a browser or use Live Server
```

## Environment Variables
``` bash 
# Database
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_HOST=localhost
DB_NAME=flashcard_app

# Flask
FLASK_SECRET_KEY=your_super_secret_key_here

# Hugging Face AI
HUGGING_FACE_TOKEN=hf_your_hugging_face_token_here

# Intasend Payments (Sandbox)
INTASEND_PUBLISHABLE_KEY=pk_test_your_key_here
INTASEND_SECRET_KEY=sk_test_your_key_here
INTASEND_WEBHOOK_SECRET=whsec_your_webhook_secret_here
```

## How to use
### Starting the application locally
### 1. Start mysql server on your machine.
### 2. Start the Backend server
``` bash
# Activate virtual environment (if created)
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run the Flask application
python app.py
```
Backend server will run on http://localhost:5000
### 3. Open the frontend
Open index.html directly in your web browser or user live server.

## Using the App
- Register/Login - Create an account or use demo credentials
- Enter Notes - Paste your study notes into the textarea
- Generate Flashcards - AI will create questions from your notes
- Study - Click flashcards to flip them and test your knowledge
- Go Premium - Upgrade for additional features (sandbox mode)

## API Endpoints
### Authentication
- POST /register - Create new user
- POST /login - User login
- POST /logout - User logout
- GET /check-auth - Check authentication status
### Flashcards
- POST /generate-flashcards - Generate flashcards from text
- GET /flashcards - Retrieve all flashcards
### Payments
- POST /create-payment-link - Create Intasend payment link
- POST /payment-webhook - Handle payment confirmation
- GET /check-premium - Check user premium status
### Health
- GET /health - API health check

## AI Prompt Engineering
Model Used: google/flan-t5-base from Hugging Face Inference API
### Engineered Prompt Template:
```
"Generate a fill-in-the-blank question: {user_input_text}"
```
### How It Works:
1. User inputs study notes: "World War II ended in 1945"
2. Our system formats the prompt: *"Generate a fill-in-the-blank question: World War II ended in 1945"*
3. Hugging Face AI returns: "World War II ended in ______"
### Example Outputs:
1. User Input:	"The capital of France is Paris"	
2. AI Generated Flashcard: "The capital of France is ______"
### Why This Approach:
- Creates interactive study cards where users recall missing information
- Works perfectly for factual content and memorization
- Consistent format across all subjects
- Ideal for educational purposes - tests actual knowledge recall
### Fallback Mechanism:
If the AI service is unavailable, we use a simple algorithm to create blanks:
1. Input: "The mitochondria is the powerhouse of the cell"
2. Fallback: "The ______ is the powerhouse of the cell"

This prompt engineering approach creates effective study tools that help users actively recall information rather than passively recognize it.

## Payment Integration
Test Card Details:
- Card: 4242 4242 4242 4242
- Expiry: Any future date
- CVV: Any 3 digits
- OTP: Any 6 digits

Payment Flow
- User clicks "Go Premium"
- Creates payment link with Intasend
- User completes payment in sandbox
- Intasend sends webhook to /payment-webhook
- System upgrades user to premium

## Database Schema
### Users Table 
```
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_premium BOOLEAN DEFAULT FALSE,
    date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
### Decks Table
```
CREATE TABLE decks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    is_public BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```
### Flashcards Table
```
CREATE TABLE flashcards (
    id INT AUTO_INCREMENT PRIMARY KEY,
    deck_id INT NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (deck_id) REFERENCES decks(id) ON DELETE CASCADE
);
```
### Security Features
- Password hashing with bcrypt
- Environment variables for secrets
- SQL injection prevention with parameterized queries
- CORS configuration
- Session management with secure cookies
- Webhook signature verification (ready for production)
### Common Issues
1. ModuleNotFoundError:
```
bash
pip install -r requirements.txt
```
2. MySQL Connection Error:
- Check MySQL is running
- Verify database credentials in .env
3. Hugging Face API Errors:
- Check internet connection
- Verify API token is valid
4. Intasend Webhook Issues:
- Use ngrok for local testing: ngrok http 5000
- Or use the /simulate-payment endpoint for demos

## Debug Mode
Enable debug logging by setting debug=True in app.py:
``` python
if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

## License
This project was created for educational purposes as part of a hackathon submission. 
See the [LICENSE](LICENSE) file for details

## Team

**Austin** ([GitHub @Hlaustink](https://github.com/Hlaustink))
- Primary: Backend Architecture, AI Integration, Database Design
- Contributions: Flask API, Hugging Face integration, MySQL optimization

**Natalie** ([GitHub @Keli281](https://github.com/Keli281))  
- Primary: Frontend Development, UI/UX Design, User Experience
- Contributions: JavaScript functionality, CSS animations, HTML structure

**Collaboration**: Both team members contributed to full-stack development, code review, and feature implementation across all layers of the application.