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
