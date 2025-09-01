-- All SQL commands to set up the database from scratch
-- Run this file before starting the Flask application

-- Create the database
CREATE DATABASE IF NOT EXISTS flashcard_app;
USE flashcard_app;

-- Table to store user information
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_premium BOOLEAN DEFAULT FALSE,
    date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table to store flashcard decks
CREATE TABLE IF NOT EXISTS decks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    is_public BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Table to store individual flashcards
CREATE TABLE IF NOT EXISTS flashcards (
    id INT AUTO_INCREMENT PRIMARY KEY,
    deck_id INT NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (deck_id) REFERENCES decks(id) ON DELETE CASCADE
);

-- Table to store payment information
CREATE TABLE payments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    invoice_id VARCHAR(255) NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(10) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Add indexes for better query performance
CREATE INDEX idx_decks_user_id ON decks(user_id);
CREATE INDEX idx_flashcards_deck_id ON flashcards(deck_id);

-- Insert default user and deck FIRST
INSERT IGNORE INTO users (id, username, email, password_hash, is_premium) VALUES 
(1, 'demo_user', 'demo@example.com', '$2b$12$EXAMPLEHASHEDPASSWORD1234567890', FALSE);

INSERT IGNORE INTO decks (id, user_id, title, description, is_public) VALUES 
(1, 1, 'Default Deck', 'Automatically created default deck for flashcards', FALSE);

-- THEN insert sample flashcards
INSERT IGNORE INTO flashcards (deck_id, question, answer) VALUES
(1, 'What is the capital of France?', 'Paris'),
(1, 'What is the largest planet in our solar system?', 'Jupiter'),
(1, 'Who wrote Romeo and Juliet?', 'William Shakespeare');