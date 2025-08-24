// Scroll chat to bottom on load
const chatWindow = document.getElementById('chat-window');
if (chatWindow) chatWindow.scrollTop = chatWindow.scrollHeight;

// Get form elements
const chatForm = document.getElementById('chat-form');
const textarea = chatForm.querySelector('textarea[name="user_message"]');
const sendButton = document.getElementById('send-button');
const sendIcon = document.getElementById('send-icon');
const spinner = document.getElementById('spinner');

// NEW: Photo upload elements
const photoBtn = document.getElementById('photoBtn');
const photoInput = document.getElementById('photoInput');
const photoUploadSection = document.getElementById('photoUploadSection');
const photoPreview = document.getElementById('photoPreview');
const plantSelect = document.getElementById('plantSelect');
const plantIdInput = document.getElementById('plantIdInput');

// NEW: Photo upload functionality
let selectedPhoto = null;

photoBtn.addEventListener('click', function() {
    photoInput.click();
});

photoInput.addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (file) {
        handlePhotoSelect(file);
    }
});

// Handle drag and drop for photos
photoUploadSection.addEventListener('dragover', function(e) {
    e.preventDefault();
    photoUploadSection.classList.add('dragover');
});

photoUploadSection.addEventListener('dragleave', function(e) {
    e.preventDefault();
    photoUploadSection.classList.remove('dragover');
});

photoUploadSection.addEventListener('drop', function(e) {
    e.preventDefault();
    photoUploadSection.classList.remove('dragover');

    const files = e.dataTransfer.files;
    if (files.length > 0 && files[0].type.startsWith('image/')) {
        photoInput.files = files;
        handlePhotoSelect(files[0]);
    }
});

function handlePhotoSelect(file) {
    selectedPhoto = file;

    // Show photo upload section
    photoUploadSection.style.display = 'block';
    photoBtn.classList.add('active');

    // Create preview
    const reader = new FileReader();
    reader.onload = function(e) {
        photoPreview.innerHTML = `
            <img src="${e.target.result}" alt="Photo preview">
            <p><strong>${file.name}</strong> (${(file.size / 1024 / 1024).toFixed(2)} MB)</p>
            <button type="button" onclick="clearPhotoSelection()" class="btn btn-sm btn-secondary">
                <i class="fas fa-times"></i> Remove
            </button>
        `;
    };
    reader.readAsDataURL(file);

    // Update placeholder text
    textarea.placeholder = "Describe what you'd like me to analyze in this photo...";
}

function clearPhotoSelection() {
    selectedPhoto = null;
    photoInput.value = '';
    photoUploadSection.style.display = 'none';
    photoBtn.classList.remove('active');
    photoPreview.innerHTML = '';
    plantIdInput.value = '';
    plantSelect.value = '';
    textarea.placeholder = "Type a message or upload a photo for analysis...";
}

// Update plant selection
plantSelect.addEventListener('change', function() {
    plantIdInput.value = this.value;
});

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
            <span class="typing-text">${selectedPhoto ? 'PlantPal is analyzing your photo' : 'PlantPal is thinking'}</span>
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
    if (photoBtn) photoBtn.disabled = true;
}

// Function to hide loading state
function hideLoadingState() {
    sendButton.disabled = false;
    sendIcon.style.display = 'block';
    spinner.style.display = 'none';
    textarea.disabled = false;
    if (photoBtn) photoBtn.disabled = false;
}

// Handle form submission
chatForm.addEventListener('submit', function(e) {
    e.preventDefault();

    const messageText = textarea.value.trim();

    // Require either text message or photo
    if (messageText === '' && !selectedPhoto) {
        return;
    }

    // Show loading state
    showLoadingState();

    // Add user message to chat immediately (NEW: Handle photo messages)
    const userRow = document.createElement('div');
    userRow.className = 'chat-row user';

    let messageContent = '';
    if (selectedPhoto) {
        messageContent = `📸 <em>Uploaded photo: ${selectedPhoto.name}</em><br>`;
    }
    messageContent += messageText || 'Please analyze this photo';

    userRow.innerHTML = `
        <div class="chat-bubble user-bubble">
            ${messageContent}
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

    // Submit form after a short delay to show the typing indicator
    setTimeout(() => {
        // If we have a photo but no text, add a default message
        if (selectedPhoto && !messageText) {
            textarea.value = 'Please analyze this photo for any plant health issues.';
        }

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

// NEW: Add quick photo analysis buttons for recent messages
function addPhotoAnalysisButtons() {
    // This function can be called to add analysis buttons to photo messages
    const photoMessages = document.querySelectorAll('.chat-bubble:contains("📸")');
    photoMessages.forEach(message => {
        if (!message.querySelector('.photo-actions')) {
            const actions = document.createElement('div');
            actions.className = 'photo-actions';
            actions.innerHTML = `
                <button onclick="requestPhotoReanalysis()" class="btn btn-sm btn-secondary">
                    <i class="fas fa-redo"></i> Re-analyze
                </button>
            `;
            message.appendChild(actions);
        }
    });
}

function requestPhotoReanalysis() {
    textarea.value = 'Can you provide a more detailed analysis of my recent photo?';
    chatForm.dispatchEvent(new Event('submit'));
}

// NEW: Add quick photo analysis buttons for recent messages
function addPhotoAnalysisButtons() {
    // This function can be called to add analysis buttons to photo messages
    const photoMessages = document.querySelectorAll('.chat-bubble:contains("📸")');
    photoMessages.forEach(message => {
        if (!message.querySelector('.photo-actions')) {
            const actions = document.createElement('div');
            actions.className = 'photo-actions';
            actions.innerHTML = `
                <button onclick="requestPhotoReanalysis()" class="btn btn-sm btn-secondary">
                    <i class="fas fa-redo"></i> Re-analyze
                </button>
            `;
            message.appendChild(actions);
        }
    });
}

function requestPhotoReanalysis() {
    textarea.value = 'Can you provide a more detailed analysis of my recent photo?';
    chatForm.dispatchEvent(new Event('submit'));
}