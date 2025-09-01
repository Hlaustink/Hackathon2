## Flashcard AI Generator 🚀
A full-stack web application that uses AI to automatically generate flashcards from study notes. Built for the hackathon with a focus on SDG 4 (Quality Education).

## Features Used
- AI-Powered: Uses Hugging Face transformers to generate questions from notes
- User Authentication: Secure login/registration with password hashing
- Monetization Ready: Intasend integration for premium features
- Professional Grade: Connection pooling, error handling, and security best practices
- Responsive Design: Clean UI with flip-card animations

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
