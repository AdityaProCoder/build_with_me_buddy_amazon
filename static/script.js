// static/script.js
document.addEventListener('DOMContentLoaded', () => {
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
                typeSpeed = 2000;
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

    const chatbotContainer = document.getElementById('chatbot-container');
    const chatbotToggle = document.getElementById('chatbot-toggle');
    const chatWindow = document.getElementById('chat-window');
    const closeBtn = document.getElementById('chat-close-btn');
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const chatMessages = document.getElementById('chat-messages');
    const pageOverlay = document.getElementById('page-overlay');

    let conversationState = 'start';
    let isExpanded = false;

    chatbotToggle.addEventListener('click', () => {
        chatWindow.style.display = 'flex';
        chatbotToggle.style.display = 'none';
        chatInput.focus();
    });

    function closeChat() {
        chatWindow.style.display = 'none';
        chatbotToggle.style.display = 'flex';
        chatbotContainer.classList.remove('expanded');
        pageOverlay.classList.remove('visible');
        isExpanded = false;
        conversationState = 'start'; // Reset state on close
    }

    closeBtn.addEventListener('click', closeChat);
    pageOverlay.addEventListener('click', closeChat);

    chatInput.addEventListener('input', () => {
        if (!isExpanded && chatInput.value.length > 0) {
            chatbotContainer.classList.add('expanded');
            pageOverlay.classList.add('visible');
            isExpanded = true;
        }
    });

    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const userMessage = chatInput.value.trim();
        const userInputLower = userMessage.toLowerCase();
        if (!userMessage) return;

        addMessage(userMessage, 'user-message');
        chatInput.value = '';
        showTypingIndicator();

        let endpoint = '';
        let body = {};
        const isConfirmation = ['looks good', 'proceed', 'yes', 'continue', 'ok'].includes(userInputLower);

        // State machine to determine which endpoint to call
        if (conversationState === 'start') {
            endpoint = '/kickoff_crew';
            body = { project_details: userMessage };
        } else if (conversationState === 'awaiting_bom' && isConfirmation) {
            endpoint = '/generate_bom';
        } else if (conversationState === 'awaiting_final_assets' && isConfirmation) {
            endpoint = '/generate_final_assets';
        } else {
            // Handle cases where confirmation is expected but not given
            removeTypingIndicator();
            addMessage("Please type 'Proceed' to continue, or start a new project description.", 'bot-message');
            return;
        }

        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body),
            });

            removeTypingIndicator();
            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.details || `Server error: ${response.status}`);
            }

            const data = await response.json();

            if (data.result) addMessage(data.result, 'bot-message');
            if (data.prompt) addPromptMessage(data.prompt);

            // Update conversation state based on the successful API call
            if (endpoint === '/kickoff_crew') {
                conversationState = 'awaiting_bom';
            } else if (endpoint === '/generate_bom') {
                conversationState = 'awaiting_final_assets';
            } else if (endpoint === '/generate_final_assets') {
                conversationState = 'start'; // Cycle is complete, ready for a new project
            }
        } catch (error) {
            console.error("Error fetching from API:", error);
            addMessage(`Sorry, an error occurred: ${error.message}`, 'bot-message');
            removeTypingIndicator();
            conversationState = 'start'; // Reset state on error
        }
    });

    function addMessage(text, className) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', className);

        let html = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

        html = html.replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank">$1</a>');

        html = html.replace(/\n/g, '<br>');

        messageDiv.innerHTML = html;
        chatMessages.appendChild(messageDiv);
        scrollToBottom();
    }

    function addPromptMessage(text) {
        const promptDiv = document.createElement('div');
        promptDiv.classList.add('message', 'bot-message', 'prompt-message');
        promptDiv.textContent = text;
        chatMessages.appendChild(promptDiv);
        scrollToBottom();
    }

    function showTypingIndicator() {
        if (chatMessages.querySelector('.typing-indicator')) return;
        const indicator = document.createElement('div');
        indicator.classList.add('message', 'bot-message', 'typing-indicator');
        indicator.innerHTML = '<span></span><span></span><span></span>';
        chatMessages.appendChild(indicator);
        scrollToBottom();
    }

    function removeTypingIndicator() {
        const indicator = chatMessages.querySelector('.typing-indicator');
        if (indicator) indicator.remove();
    }

    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
});
