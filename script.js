document.addEventListener('DOMContentLoaded', function() {
    // --- DOM Elements ---
    const notesInput = document.getElementById('notes-input');
    const generateBtn = document.getElementById('generate-btn');
    const exportBtn = document.getElementById('export-btn');
    const clearBtn = document.getElementById('clear-btn');
    const flashcardsContainer = document.getElementById('flashcards-container');
    const loadingElement = document.getElementById('loading');
    const notification = document.getElementById('notification');
    const languageSelect = document.getElementById('language'); // Assuming you have an element with id="language"

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
        flashcardsContainer.innerHTML = ''; // Clear previous results immediately

        try {
            const response = await fetch('http://localhost:5000/generate-flashcards', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ notes: notes, language: language })
            });
            
            const data = await response.json();

            // Handle non-ok HTTP statuses (like 400, 500)
            if (!response.ok) {
                // Use the error message from the backend if available
                throw new Error(data.error || 'An unknown error occurred.');
            }

            if (!data.flashcards || data.flashcards.length === 0) {
                 showNotification('Could not generate flashcards. Please try different text.', 'error');
                 return;
            }

            // Display the generated flashcards
            data.flashcards.forEach(card => createFlashcard(card.question, card.answer));
            showNotification('Flashcards generated successfully!');

        } catch (error) {
            console.error('Fetch Error:', error);
            showNotification(`Error: ${error.message}. Showing demo cards.`, 'error');
            // Fallback to demo data on error
            sampleFlashcards.forEach(card => createFlashcard(card.question, card.answer));
        } finally {
            // Revert UI from loading state
            setLoading(false);
        }
    }

    function handleExport() {
        if (flashcardsContainer.children.length === 0) {
            showNotification('No flashcards to export!', 'error');
            return;
        }
        // This is a placeholder for a real export feature
        showNotification('Export feature is a demo.', 'success');
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
        notification.className = `notification show ${type}`; // Use classes for styling
        
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
