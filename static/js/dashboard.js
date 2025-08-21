// Dashboard functionality for Plant Care Task Management

let currentDate = new Date();
let taskData = {};

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard initializing...');

    // Initialize with empty data first
    window.taskData = {
        overdue_count: 0,
        today_count: 0,
        upcoming_count: 0,
        tasks: [],
        summary: {
            total_tasks: 0,
            active_tasks: 0,
            completion_rate: 0
        }
    };

    // Setup event listeners
    setupEventListeners();
    
    // Setup recurrence and frequency input logic
    setupRecurrenceLogic();

    // Load data from server
    loadTaskData();

    console.log('Dashboard initialization complete');
});

// Setup recurrence and frequency input logic
function setupRecurrenceLogic() {
    const recurrenceSelect = document.getElementById('recurrence_type');
    const frequencyInput = document.getElementById('frequency_days');

    function updateFrequencyInput() {
        if (!recurrenceSelect || !frequencyInput) return;
        
        const selectedValue = recurrenceSelect.value;
        console.log('Recurrence type changed to:', selectedValue);
        
        if (selectedValue === 'custom') {
            frequencyInput.disabled = false;
            frequencyInput.placeholder = 'Enter custom days';
            // Keep existing value or clear it
            if (!frequencyInput.value) {
                frequencyInput.value = '';
            }
        } else {
            frequencyInput.disabled = true;
            const frequency = getFrequencyForRecurrence(selectedValue);
            frequencyInput.value = frequency;
            console.log('Set frequency to:', frequency);
        }
    }

    if (recurrenceSelect && frequencyInput) {
        recurrenceSelect.addEventListener('change', updateFrequencyInput);
        updateFrequencyInput(); // Initialize the state on page load
    }
}

// Helper function to get frequency days based on recurrence type
function getFrequencyForRecurrence(recurrenceType) {
    switch (recurrenceType) {
        case 'none':
            return 0;
        case 'daily':
            return 1;
        case 'weekly':
            return 7;
        case 'monthly':
            return 30;
        case 'weekend':
            return 7; // Weekly but only weekends
        case 'custom':
            return null; // User will input
        default:
            return 0;
    }
}

// Function to ensure frequency is updated before form submission
function updateFrequencyBeforeSubmit() {
    const recurrenceSelect = document.getElementById('recurrence_type');
    const frequencyInput = document.getElementById('frequency_days');
    
    if (recurrenceSelect && frequencyInput) {
        const selectedValue = recurrenceSelect.value;
        if (selectedValue !== 'custom') {
            const frequency = getFrequencyForRecurrence(selectedValue);
            frequencyInput.value = frequency;
            console.log('Updated frequency before submit:', frequency);
        }
    }
}

// Load task data from server
async function loadTaskData() {
    try {
        console.log('Loading task data...');
        const response = await fetch('/dashboard/');

        console.log('Response status:', response.status);

        if (!response.ok) {
            const errorText = await response.text();
            console.error('Response error text:', errorText);
            throw new Error(`HTTP error! status: ${response.status}, text: ${errorText}`);
        }

        const data = await response.json();
        console.log('Received task data:', data);

        // Store the data globally
        window.taskData = data;

        // Update UI with new data
        updateTaskStats();
        renderTaskList();

        console.log('Task data loaded successfully');
    } catch (error) {
        console.error('Error loading task data:', error);
        // Keep the default empty data structure if API fails
        console.log('Keeping default empty data structure');
    }
}

// Update task statistics
function updateTaskStats() {
    console.log('Updating task stats with data:', window.taskData);

    const overdueElement = document.querySelector('.stat-card.overdue .stat-number');
    const todayElement = document.querySelector('.stat-card.today .stat-number');
    const finishedElement = document.querySelector('.stat-card.finished .stat-number');
    const upcomingElement = document.querySelector('.stat-card.upcoming .stat-number');

    if (overdueElement) {
        overdueElement.textContent = window.taskData.overdue_count || 0;
    }

    if (todayElement) {
        todayElement.textContent = window.taskData.today_count || 0;
    }
    if (finishedElement) {
        finishedElement.textContent = window.taskData.completed_count || 0;
    }

    if (upcomingElement) {
        upcomingElement.textContent = window.taskData.upcoming_count || 0;
    }
}

// Render task list
function renderTaskList() {
    // This function can be expanded to render tasks dynamically
    // For now, it's a placeholder since tasks are rendered server-side
    console.log('Rendering task list...');
}

// Setup event listeners
function setupEventListeners() {
    console.log('Setting up event listeners...');

    // Task form submission
    const taskForm = document.getElementById('task-form');
    if (taskForm) {
        taskForm.addEventListener('submit', handleTaskSubmit);
    }

    console.log('Event listeners setup complete');
}

// Task view modal functions
function openTaskViewModal(filterType = 'today') {
    const modal = document.getElementById('task-view-modal');
    modal.classList.remove('hidden');
    document.body.style.overflow = 'hidden';

    // Switch to the requested filter
    switchTaskFilter(filterType);
}

function closeTaskViewModal() {
    const modal = document.getElementById('task-view-modal');
    modal.classList.add('hidden');
    document.body.style.overflow = 'auto';
}

function switchTaskFilter(filterType) {
    // Update title
    const title = document.getElementById('task-view-title');
    const titleMap = {
        'delayed': 'Delayed Tasks',
        'today': "Today's Tasks",
        'completed': 'Completed Tasks',
        'upcoming': 'Upcoming Tasks'
    };
    title.textContent = titleMap[filterType] || "Today's Tasks";

    // Update active tab
    document.querySelectorAll('.filter-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelector(`[data-filter="${filterType}"]`).classList.add('active');

    // Update active stat card
    document.querySelectorAll('.stat-card').forEach(card => {
        card.classList.remove('active');
    });
    const cardMap = {
        'delayed': 'overdue',
        'today': 'today',
        'completed': 'finished',
        'upcoming': 'upcoming'
    };
    document.querySelector(`.stat-card.${cardMap[filterType]}`).classList.add('active');

    // Show corresponding task group
    document.querySelectorAll('.task-group').forEach(group => {
        group.classList.add('hidden');
    });
    document.getElementById(`${filterType === 'delayed' ? 'delayed' : filterType}-tasks`).classList.remove('hidden');
}

// Task modal functions
function openTaskModal(taskId = null) {
    const modal = document.getElementById('task-modal');
    const title = document.getElementById('modal-title');
    const form = document.getElementById('task-form');

    if (taskId) {
        title.textContent = 'Edit Task';
        // Store task ID for editing
        form.setAttribute('data-task-id', taskId);
        // Load existing task data
        loadTaskForEditing(taskId);
    } else {
        title.textContent = 'Add New Task';
        form.reset();
        form.removeAttribute('data-task-id');
        // Reset the frequency input logic
        setupRecurrenceLogic();
    }

    modal.classList.remove('hidden');
    document.body.style.overflow = 'hidden'; // Prevent background scrolling
}

// Load existing task data for editing
async function loadTaskForEditing(taskId) {
    try {
        console.log('Loading task for editing:', taskId);
        const response = await fetch(`/dashboard/tasks/${taskId}`);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const task = await response.json();
        console.log('Loaded task data:', task);

        // Populate form fields with existing data
        populateTaskForm(task);

    } catch (error) {
        console.error('Error loading task for editing:', error);
        showMessage('Failed to load task data. Please try again.', 'error');
        closeTaskModal();
    }
}

// Populate the task form with existing data
function populateTaskForm(task) {
    const form = document.getElementById('task-form');

    // Populate form fields
    const fields = {
        'plant_id': task.plant_id,
        'task_type': task.task_type,
        'title': task.title,
        'description': task.description || '',
        'recurrence_type': task.recurrence_type || 'none',
        'frequency_days': task.frequency_days || 0
    };

    // Set form field values
    Object.keys(fields).forEach(fieldName => {
        const field = form.querySelector(`[name="${fieldName}"]`);
        if (field) {
            field.value = fields[fieldName];
        }
    });

    // Update frequency input based on recurrence type
    setTimeout(() => {
        setupRecurrenceLogic();
        // If it's a custom recurrence, make sure the frequency field shows the actual value
        if (task.recurrence_type === 'custom') {
            const frequencyInput = document.getElementById('frequency_days');
            if (frequencyInput) {
                frequencyInput.value = task.frequency_days || '';
            }
        }
    }, 100);
}

function closeTaskModal() {
    const modal = document.getElementById('task-modal');
    modal.classList.add('hidden');
    document.body.style.overflow = 'auto'; // Restore scrolling
}

// Handle task form submission
async function handleTaskSubmit(e) {
    e.preventDefault();

    const form = e.target;
    const taskId = form.getAttribute('data-task-id');
    const isEditing = !!taskId;

    const formData = new FormData(form);
    const rawData = Object.fromEntries(formData.entries());

    console.log('Raw form data:', rawData);
    console.log('Is editing:', isEditing, 'Task ID:', taskId);

    // Ensure frequency_days is set based on recurrence_type before submitting
    updateFrequencyBeforeSubmit();

    // Convert and clean the data for the API
    const taskData = {
        plant_id: parseInt(rawData.plant_id),
        task_type: rawData.task_type,
        title: rawData.title,
        description: rawData.description || null,
        recurrence_type: rawData.recurrence_type,
        frequency_days: rawData.frequency_days ? parseInt(rawData.frequency_days) : getFrequencyForRecurrence(rawData.recurrence_type),
        is_active: true
    };

    // Remove null/empty values
    Object.keys(taskData).forEach(key => {
        if (taskData[key] === null || taskData[key] === '') {
            delete taskData[key];
        }
    });

    console.log('Sending task data:', taskData);

    try {
        const url = isEditing ? `/dashboard/tasks/${taskId}` : '/dashboard/tasks';
        const method = isEditing ? 'PUT' : 'POST';

        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(taskData)
        });

        console.log('Response status:', response.status);

        if (response.ok) {
            closeTaskModal();
            const message = isEditing ? 'Task updated successfully!' : 'Task saved successfully!';
            showMessage(message, 'success');
            location.reload();  // Refresh the template with updated data
        } else {
            const errorData = await response.json();
            console.error('Server error:', errorData);
            const action = isEditing ? 'update' : 'save';
            showMessage(`Failed to ${action} task: ${errorData.detail || 'Unknown error'}`, 'error');
        }
    } catch (error) {
        console.error('Error saving/updating task:', error);
        const action = isEditing ? 'update' : 'save';
        showMessage(`Failed to ${action} task. Please try again.`, 'error');
    }
}

// Complete task function
async function completeTask(taskId, isCompleted = true) {
    try {
        const response = await fetch(`/dashboard/tasks/${taskId}/complete`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                is_completed: isCompleted
            })
        });

        if (response.ok) {
            showMessage('Task status updated successfully!', 'success');
            location.reload();
        } else {
            throw new Error('Failed to update task status');
        }
    } catch (error) {
        console.error('Error updating task status:', error);
        showMessage('Failed to update task status.', 'error');
    }
}

// Delete task function
async function deleteTask(taskId) {
    if (!confirm('Are you sure you want to delete this task?')) return;

    try {
        const response = await fetch(`/dashboard/tasks/${taskId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            showMessage('Task deleted successfully!', 'success');
            location.reload();
        }
    } catch (error) {
        console.error('Error deleting task:', error);
        showMessage('Failed to delete task.', 'error');
    }
}

// Show message function
function showMessage(message, type) {
    // Create a toast notification
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    
    // Add styles
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 12px 24px;
        border-radius: 8px;
        color: white;
        font-weight: 600;
        z-index: 10000;
        animation: slideIn 0.3s ease-out;
        ${type === 'success' ? 'background: #27ae60;' : 'background: #e74c3c;'}
    `;
    
    document.body.appendChild(toast);
    
    // Remove after 3 seconds
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }, 3000);
}

// Add CSS for toast animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);