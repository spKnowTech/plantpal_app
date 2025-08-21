// Scroll chat to bottom on load
const chatWindow = document.getElementById('chat-window');
if (chatWindow) chatWindow.scrollTop = chatWindow.scrollHeight;

// Get form elements
const chatForm = document.getElementById('chat-form');
const textarea = chatForm.querySelector('textarea[name="user_message"]');
const sendButton = document.getElementById('send-button');
const sendIcon = document.getElementById('send-icon');
const spinner = document.getElementById('spinner');

// Function to show typing indicator
function showTypingIndicator() {
    const typingRow = document.createElement('div');
    typingRow.className = 'chat-row bot';
    typingRow.id = 'typing-indicator';

    typingRow.innerHTML = `
        <span class="chat-avatar">
            <i class="fas fa-seedling"></i>
        </span>
        <div class="typing-indicator">
            <span class="typing-text">PlantPal is thinking</span>
            <div class="typing-dots">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        </div>
    `;

    chatWindow.appendChild(typingRow);
    chatWindow.scrollTop = chatWindow.scrollHeight;
}

// Function to hide typing indicator
function hideTypingIndicator() {
    const typingIndicator = document.getElementById('typing-indicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

// Function to show loading state
function showLoadingState() {
    sendButton.disabled = true;
    sendIcon.style.display = 'none';
    spinner.style.display = 'block';
    textarea.disabled = true;
}

// Function to hide loading state
function hideLoadingState() {
    sendButton.disabled = false;
    sendIcon.style.display = 'block';
    spinner.style.display = 'none';
    textarea.disabled = false;
}

// Handle form submission
chatForm.addEventListener('submit', function(e) {
    e.preventDefault();

    const messageText = textarea.value.trim();
    if (messageText === '') return;

    // Show loading state
    showLoadingState();

    // Add user message to chat immediately
    const userRow = document.createElement('div');
    userRow.className = 'chat-row user';
    userRow.innerHTML = `
        <div class="chat-bubble user-bubble">
            ${messageText}
            <div class="message-time">Now</div>
        </div>
        <span class="chat-avatar user-avatar">
            <i class="fas fa-user"></i>
        </span>
    `;

    chatWindow.appendChild(userRow);
    chatWindow.scrollTop = chatWindow.scrollHeight;

    // Show typing indicator
    showTypingIndicator();

    // Create a hidden input to preserve the message for form submission
    const hiddenInput = document.createElement('input');
    hiddenInput.type = 'hidden';
    hiddenInput.name = 'user_message';
    hiddenInput.value = messageText;
    chatForm.appendChild(hiddenInput);

    // Clear the visible textarea
    textarea.value = '';

    // Submit form after a short delay to show the typing indicator
    setTimeout(() => {
        chatForm.submit();
    }, 500);
});

// Auto-submit on Enter key (but allow Shift+Enter for new line)
textarea.addEventListener('keypress', function(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        chatForm.dispatchEvent(new Event('submit'));
    }
});

// Auto-resize textarea as user types
textarea.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 120) + 'px'; // Max height of 120px
});

// Focus textarea on page load
window.addEventListener('load', function() {
    textarea.focus();
});

// Check if page is reloading after form submission
if (performance.navigation.type === 1) {
    // Page was reloaded, hide any existing typing indicator
    hideTypingIndicator();
}