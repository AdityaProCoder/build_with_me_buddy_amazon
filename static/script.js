// static/script.js
document.addEventListener('DOMContentLoaded', () => {
    // --- Typewriter Effect Logic ---
    const typewriterElement = document.getElementById('typewriter-hero');
    const phrases = ["Innovate.", "Create.", "Inspire."];

    function runTypewriter() {
        if (!typewriterElement) return;
        let phraseIndex = 0;
        let charIndex = 0;
        let isDeleting = false;

        function type() {
            const fullPhrase = phrases[phraseIndex];
            let currentPhrase = '';

            if (isDeleting) {
                currentPhrase = fullPhrase.substring(0, charIndex - 1);
                charIndex--;
            } else {
                currentPhrase = fullPhrase.substring(0, charIndex + 1);
                charIndex++;
            }

            typewriterElement.textContent = currentPhrase;
            let typeSpeed = isDeleting ? 100 : 200;

            if (!isDeleting && charIndex === fullPhrase.length) {
                typeSpeed = 2000; // Pause after word is typed
                isDeleting = true;
            } else if (isDeleting && charIndex === 0) {
                isDeleting = false;
                phraseIndex = (phraseIndex + 1) % phrases.length;
            }
            setTimeout(type, typeSpeed);
        }
        type();
    }

    runTypewriter();

    // --- Chatbot UI and State Elements ---
    const chatbotContainer = document.getElementById('chatbot-container');
    const chatbotToggle = document.getElementById('chatbot-toggle');
    const chatWindow = document.getElementById('chat-window');
    const closeBtn = document.getElementById('chat-close-btn');
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const chatMessages = document.getElementById('chat-messages');
    const pageOverlay = document.getElementById('page-overlay');

    // --- State Management ---
    let isExpanded = false;
    let isAwaitingConfirmation = false; // Manages the two-part crew flow

    // --- Event Listeners for UI ---

    // Open the initial small chat pop-up
    chatbotToggle.addEventListener('click', () => {
        chatWindow.style.display = 'flex';
        chatbotToggle.style.display = 'none';
        chatInput.focus();
    });

    // Function to close the chat window and reset everything
    function closeChat() {
        chatWindow.style.display = 'none';
        chatbotToggle.style.display = 'flex';
        chatbotContainer.classList.remove('expanded');
        pageOverlay.classList.remove('visible');
        isExpanded = false;
        isAwaitingConfirmation = false; // Reset state on close
    }

    closeBtn.addEventListener('click', closeChat);
    pageOverlay.addEventListener('click', closeChat); // Close chat when clicking overlay

    // Expand chat to centered modal on first character input
    chatInput.addEventListener('input', () => {
        if (!isExpanded && chatInput.value.length > 0) {
            chatbotContainer.classList.add('expanded');
            pageOverlay.classList.add('visible');
            isExpanded = true;
        }
    });

    // --- Main Form Submission Logic ---
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const userMessage = chatInput.value.trim();
        const userInputLower = userMessage.toLowerCase();

        if (!userMessage) return;

        addMessage(userMessage, 'user-message');
        chatInput.value = '';
        showTypingIndicator();

        let endpoint = '/kickoff_crew';
        let body = { project_details: userMessage };

        // Logic to choose the correct endpoint based on conversation state
        const confirmationPhrases = ['looks good', 'proceed', 'yes', 'continue', 'ok'];
        if (isAwaitingConfirmation && confirmationPhrases.includes(userInputLower)) {
            endpoint = '/continue_crew';
            body = {}; // Data is already on the server in the session
        } else {
            isAwaitingConfirmation = false; // Treat as a new request
        }

        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body),
            });

            removeTypingIndicator();
            if (!response.ok) throw new Error(`Server error: ${response.status}`);

            const data = await response.json();

            // Handle structured response from the server
            if (data.result) {
                addMessage(data.result, 'bot-message');
            }
            if (data.prompt) {
                addPromptMessage(data.prompt);
            }

            // Update state based on which endpoint was called
            if (endpoint === '/kickoff_crew') {
                isAwaitingConfirmation = true; // Now waiting for user approval
            } else {
                isAwaitingConfirmation = false; // Crew finished, reset state
            }

        } catch (error) {
            console.error("Error fetching from API:", error);
            addMessage("Sorry, I'm having trouble connecting. Please try again later.", 'bot-message');
            removeTypingIndicator();
            isAwaitingConfirmation = false; // Reset state on any error
        }
    });

    // --- Helper Functions ---

    // Adds a standard user or bot message to the chat
    function addMessage(text, className) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', className);
        // Use innerHTML to correctly render markdown-like bolding for headlines
        messageDiv.innerHTML = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        chatMessages.appendChild(messageDiv);
        scrollToBottom();
    }

    // Adds the special, styled prompt message
    function addPromptMessage(text) {
        const promptDiv = document.createElement('div');
        promptDiv.classList.add('message', 'bot-message', 'prompt-message');
        promptDiv.textContent = text;
        chatMessages.appendChild(promptDiv);
        scrollToBottom();
    }

    // Shows the "..." typing indicator
    function showTypingIndicator() {
        if (chatMessages.querySelector('.typing-indicator')) return; // Don't add multiple
        const indicator = document.createElement('div');
        indicator.classList.add('message', 'bot-message', 'typing-indicator');
        indicator.innerHTML = '<span></span><span></span><span></span>';
        chatMessages.appendChild(indicator);
        scrollToBottom();
    }

    // Removes the typing indicator
    function removeTypingIndicator() {
        const indicator = chatMessages.querySelector('.typing-indicator');
        if (indicator) indicator.remove();
    }

    // Auto-scrolls the chat window to the bottom
    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
});