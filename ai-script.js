document.addEventListener('DOMContentLoaded', function() {
    // --- DOM Elements ---
    const notesInput = document.getElementById('notes-input');
    const generateBtn = document.getElementById('generate-btn');
    const exportBtn = document.getElementById('export-btn');
    const clearBtn = document.getElementById('clear-btn');
    const flashcardsContainer = document.getElementById('flashcards-container');
    const loadingElement = document.getElementById('loading');
    const notification = document.getElementById('notification');
    const languageSelect = document.getElementById('language');

    // --- Sample Data for Fallback ---
    const sampleFlashcards = [
        { question: "What is the capital of France?", answer: "Paris" },
        { question: "What is the largest planet in our solar system?", answer: "Jupiter" },
        { question: "Who wrote 'Romeo and Juliet'?", answer: "William Shakespeare" },
    ];

    // --- Event Listeners ---
    generateBtn.addEventListener('click', handleGenerateFlashcards);
    exportBtn.addEventListener('click', handleExport);
    clearBtn.addEventListener('click', handleClear);

    // --- Event Handlers ---
    async function handleGenerateFlashcards() {
        const notes = notesInput.value.trim();
        const language = languageSelect.value;

        if (!notes) {
            showNotification('Please enter some notes first!', 'error');
            return;
        }

        // Set UI to loading state
        setLoading(true);
        flashcardsContainer.innerHTML = '';

        try {
            const response = await fetch('http://localhost:5000/generate-flashcards', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ notes: notes, language: language })
            });
            
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'An unknown error occurred.');
            }

            if (!data.flashcards || data.flashcards.length === 0) {
                showNotification('Could not generate flashcards. Please try different text.', 'error');
                return;
            }

            data.flashcards.forEach(card => createFlashcard(card.question, card.answer));
            showNotification('Flashcards generated successfully!');

        } catch (error) {
            console.error('Fetch Error:', error);
            showNotification(`Error: ${error.message}. Showing demo cards.`, 'error');
            sampleFlashcards.forEach(card => createFlashcard(card.question, card.answer));
        } finally {
            setLoading(false);
        }
    }

    function handleExport() {
        if (flashcardsContainer.children.length === 0) {
            showNotification('No flashcards to export!', 'error');
            return;
        }

        // Collect flashcards
        const flashcards = [];
        flashcardsContainer.querySelectorAll('.flashcard').forEach(card => {
            const question = card.querySelector('.question').innerText;
            const answer = card.querySelector('.answer').innerText;
            flashcards.push({ question, answer });
        });

        // Offer JSON or PDF
        const format = prompt("Export format? Type 'json' or 'pdf':").toLowerCase();

        if (format === 'json') {
            const blob = new Blob([JSON.stringify(flashcards, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = "flashcards.json";
            a.click();
            URL.revokeObjectURL(url);
            showNotification('Exported as JSON successfully!');
        } 
        else if (format === 'pdf') {
            const doc = new jsPDF();
            doc.setFontSize(14);
            flashcards.forEach((card, idx) => {
                doc.text(`Q${idx + 1}: ${card.question}`, 10, 20 + (idx * 20));
                doc.text(`A${idx + 1}: ${card.answer}`, 10, 30 + (idx * 20));
            });
            doc.save("flashcards.pdf");
            showNotification('Exported as PDF successfully!');
        } 
        else {
            showNotification('Export canceled or invalid format.', 'error');
        }
    }

    function handleClear() {
        flashcardsContainer.innerHTML = '';
        notesInput.value = '';
        showNotification('All flashcards cleared.');
    }

    // --- UI Helper Functions ---
    function createFlashcard(question, answer) {
        const flashcard = document.createElement('div');
        flashcard.className = 'flashcard';
        flashcard.innerHTML = `
            <div class="flashcard-inner">
                <div class="flashcard-front">
                    <div class="question">${question}</div>
                    <p><small>Click to flip</small></p>
                </div>
                <div class="flashcard-back">
                    <div class="answer">${answer}</div>
                    <p><small>Click to flip back</small></p>
                </div>
            </div>`;
        
        flashcard.addEventListener('click', () => flashcard.classList.toggle('flipped'));
        flashcardsContainer.appendChild(flashcard);
    }

    function showNotification(message, type = 'success') {
        notification.textContent = message;
        notification.className = `notification show ${type}`;
        setTimeout(() => {
            notification.classList.remove('show');
        }, 3000);
    }
    
    function setLoading(isLoading) {
        loadingElement.style.display = isLoading ? 'block' : 'none';
        generateBtn.disabled = isLoading;
    }

    // --- Initial State ---
    notesInput.value = "The French Revolution was a period of radical political and societal change in France. It began with the Estates General of 1789 and ended in November 1799. Its ideas are fundamental principles of liberal democracy.";
});

async function upgradeToPremium() {
    try {
        const response = await fetch('http://localhost:5000/create-payment-link', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (data.payment_url) {
            window.location.href = data.payment_url;
        } else if (data.error) {
            showNotification('Error: ' + data.error, 'error'); // Use your notification system
        }
    } catch (error) {
        showNotification('Error creating payment link', 'error'); // Use your notification system
    }
}

// Process payment with IntaSend
function processPayment() {
    const token = localStorage.getItem('authToken');
    
    if (!token) {
        alert('Authentication required. Please log in again.');
        logout();
        return;
    }
    
    // Show loading state
    const confirmBtn = document.getElementById('payment-confirm');
    const originalText = confirmBtn.innerHTML;
    confirmBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating payment...';
    confirmBtn.disabled = true;
    
    // Create payment intent with IntaSend
    fetch('/create-payment-intent', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Redirect to IntaSend payment page
        window.location.href = data.payment_url;
        
        // Poll for payment completion
        pollPaymentStatus(data.invoice_id);
    })
    .catch(error => {
        console.error('Payment error:', error);
        alert('Payment setup failed: ' + error.message);
        
        // Reset button
        confirmBtn.innerHTML = originalText;
        confirmBtn.disabled = false;
    });
}

function pollPaymentStatus(invoiceId) {
    const token = localStorage.getItem('authToken');
    const maxAttempts = 30; // 3 minutes at 6-second intervals
    let attempts = 0;
    
    const checkStatus = setInterval(() => {
        attempts++;
        
        if (attempts > maxAttempts) {
            clearInterval(checkStatus);
            alert('Payment verification timeout. Please contact support if payment was made.');
            return;
        }
        
        fetch('/verify-payment', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ invoice_id: invoiceId })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                clearInterval(checkStatus);
                
                // Update token and user data
                localStorage.setItem('authToken', data.token);
                const userData = JSON.parse(localStorage.getItem('userData') || '{}');
                userData.tier = data.tier;
                localStorage.setItem('userData', JSON.stringify(userData));
                
                // Close modal and update UI
                document.getElementById('payment-modal').classList.remove('active');
                showTierInfo(data.tier);
                
                // Retry flashcard generation
                performFlashcardGeneration();
                
                alert('Payment successful! You now have premium access.');
            } else if (data.error && data.status === 'FAILED') {
                clearInterval(checkStatus);
                alert('Payment failed. Please try again.');
            }
            // If payment is still pending, continue polling
        })
        .catch(error => {
            console.error('Status check error:', error);
        });
    }, 6000); // Check every 6 seconds
}

                //AUTHENTICATION FLOW
    // Check authentication on AI app load
document.addEventListener('DOMContentLoaded', function() {
    checkAuthentication();
    // ... other initialization code
});

function checkAuthentication() {
    const token = localStorage.getItem('authToken');
    const userData = JSON.parse(localStorage.getItem('userData') || '{}');
    
    // Redirect to index.html if not authenticated
    if (!token || !userData.id) {
        window.location.href = 'index.html';
        return;
    }
    
    // Verify token with server
    fetch('/verify-token', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ token })
    })
    .then(response => response.json())
    .then(data => {
        if (data.authenticated) {
            // User is authenticated, proceed with app
            initializeApp(data.user);
        } else {
            // Token is invalid, redirect to index.html
            logout();
        }
    })
    .catch(error => {
        console.error('Authentication check failed:', error);
        logout();
    });
}

function initializeApp(user) {
    // Set up the AI application with user data
    document.getElementById('user-name').textContent = user.name;
    showTierInfo(user.tier);
    // ... other app initialization code
}

function logout() {
    // Clear all stored data
    localStorage.removeItem('authToken');
    localStorage.removeItem('userData');
    
    // Redirect to index.html
    window.location.href = 'index.html';
}

        //ERROR HANDLING
// Handle authentication errors
function handleAuthError(error) {
    console.error('Authentication error:', error);
    localStorage.removeItem('authToken');
    localStorage.removeItem('userData');
    window.location.href = 'index.html';
}

// Example usage in API calls
fetch('/some-protected-endpoint', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('authToken')}`
    }
})
.then(response => {
    if (response.status === 401) {
        handleAuthError('Token expired or invalid');
    }
    return response.json();
})
.catch(error => {
    handleAuthError(error);
});

        //LOGOUT FUNCTION
function logout() {
    // Clear all stored data
    localStorage.removeItem('authToken');
    localStorage.removeItem('userData');

    // Redirect to index.html
    window.location.href = 'index.html';
}