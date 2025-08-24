// Photo Gallery JavaScript functionality

document.addEventListener('DOMContentLoaded', function() {
    // Get modal elements
    const modal = document.getElementById('diagnosisModal');
    const modalContent = document.getElementById('diagnosisContent');
    const closeBtn = modal.querySelector('.close');
    const loadingOverlay = document.getElementById('loadingOverlay');

    // Close modal functionality
    closeBtn.addEventListener('click', function() {
        modal.style.display = 'none';
    });

    window.addEventListener('click', function(event) {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });

    // View diagnosis functionality
    document.querySelectorAll('.view-diagnosis').forEach(button => {
        button.addEventListener('click', function() {
            const photoId = this.getAttribute('data-photo-id');
            viewPhotoDiagnosis(photoId);
        });
    });

    // Analyze photo functionality
    document.querySelectorAll('.analyze-photo').forEach(button => {
        button.addEventListener('click', function() {
            const photoId = this.getAttribute('data-photo-id');
            analyzePhoto(photoId);
        });
    });

    // Chat about photo functionality
    document.querySelectorAll('.chat-about-photo').forEach(button => {
        button.addEventListener('click', function() {
            const photoId = this.getAttribute('data-photo-id');
            chatAboutPhoto(photoId);
        });
    });

    // Delete photo functionality
    document.querySelectorAll('.delete-photo').forEach(button => {
        button.addEventListener('click', function() {
            const photoId = this.getAttribute('data-photo-id');
            deletePhoto(photoId);
        });
    });

    // Functions
    function showLoading() {
        loadingOverlay.style.display = 'flex';
    }

    function hideLoading() {
        loadingOverlay.style.display = 'none';
    }

    function showModal(content) {
        modalContent.innerHTML = content;
        modal.style.display = 'block';
    }

    function viewPhotoDiagnosis(photoId) {
        showLoading();

        fetch(`/photo/${photoId}/diagnosis`)
            .then(response => response.json())
            .then(data => {
                hideLoading();

                if (data.success && data.diagnosis) {
                    const diagnosis = data.diagnosis;

                    let content = `
                        <h2><i class="fas fa-microscope"></i> Plant Diagnosis Report</h2>
                        <div class="diagnosis-details">
                            <div class="confidence-section">
                                <h4>Analysis Confidence</h4>
                                <div class="confidence-bar">
                                    <div class="confidence-fill" style="width: ${(diagnosis.confidence_score || 0) * 100}%"></div>
                                </div>
                                <p>${((diagnosis.confidence_score || 0) * 100).toFixed(1)}% confidence</p>
                            </div>
                    `;

                    // Add identified issues
                    if (diagnosis.identified_issues) {
                        content += '<div class="issues-section"><h4>Issues Identified</h4>';
                        for (const [category, issues] of Object.entries(diagnosis.identified_issues)) {
                            if (issues && issues.length > 0) {
                                content += `
                                    <div class="issue-category">
                                        <h5>${category.replace('_', ' ').toUpperCase()}</h5>
                                        <ul>
                                            ${issues.map(issue => `<li>${issue}</li>`).join('')}
                                        </ul>
                                    </div>
                                `;
                            }
                        }
                        content += '</div>';
                    }

                    // Add recommended actions
                    if (diagnosis.recommended_actions) {
                        content += '<div class="actions-section"><h4>Recommended Actions</h4>';
                        for (const [category, actions] of Object.entries(diagnosis.recommended_actions)) {
                            if (actions && actions.length > 0) {
                                content += `
                                    <div class="action-category">
                                        <h5>${category.replace('_', ' ').toUpperCase()}</h5>
                                        <ul>
                                            ${actions.map(action => `<li>${action}</li>`).join('')}
                                        </ul>
                                    </div>
                                `;
                            }
                        }
                        content += '</div>';
                    }

                    // Add full diagnosis text
                    content += `
                            <div class="diagnosis-text-section">
                                <h4>Full Analysis</h4>
                                <div class="diagnosis-text">${diagnosis.diagnosis_text}</div>
                            </div>

                            <div class="diagnosis-meta">
                                <p><strong>Analysis Date:</strong> ${new Date(diagnosis.created_at).toLocaleString()}</p>
                                ${diagnosis.treatment_outcome ? `<p><strong>Treatment Outcome:</strong> ${diagnosis.treatment_outcome.replace('_', ' ')}</p>` : ''}
                            </div>
                        </div>
                    `;

                    showModal(content);
                } else {
                    showModal(`
                        <h2>No Diagnosis Available</h2>
                        <p>This photo hasn't been analyzed yet.</p>
                        <button onclick="analyzePhoto(${photoId})" class="btn btn-primary">
                            <i class="fas fa-microscope"></i> Analyze Now
                        </button>
                    `);
                }
            })
            .catch(error => {
                hideLoading();
                console.error('Error fetching diagnosis:', error);
                showModal(`
                    <h2>Error</h2>
                    <p>Failed to load diagnosis. Please try again.</p>
                `);
            });
    }

    function analyzePhoto(photoId) {
        showLoading();

        const formData = new FormData();
        formData.append('user_message', 'Please provide a detailed analysis of this plant photo');

        fetch(`/analyze_photo/${photoId}`, {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            hideLoading();

            if (data.success) {
                showModal(`
                    <h2><i class="fas fa-check-circle"></i> Analysis Complete</h2>
                    <div class="analysis-result">
                        ${data.analysis}
                    </div>
                    <div class="modal-actions">
                        <button onclick="location.reload()" class="btn btn-primary">
                            <i class="fas fa-refresh"></i> Refresh Gallery
                        </button>
                        <button onclick="chatAboutPhoto(${photoId})" class="btn btn-secondary">
                            <i class="fas fa-comments"></i> Continue in Chat
                        </button>
                    </div>
                `);
            } else {
                showModal(`
                    <h2><i class="fas fa-exclamation-triangle"></i> Analysis Failed</h2>
                    <p>${data.error || 'Unknown error occurred'}</p>
                    <button onclick="analyzePhoto(${photoId})" class="btn btn-primary">
                        <i class="fas fa-redo"></i> Try Again
                    </button>
                `);
            }
        })
        .catch(error => {
            hideLoading();
            console.error('Error analyzing photo:', error);
            showModal(`
                <h2>Error</h2>
                <p>Failed to analyze photo. Please try again.</p>
                <button onclick="analyzePhoto(${photoId})" class="btn btn-primary">
                    <i class="fas fa-redo"></i> Try Again
                </button>
            `);
        });
    }

    function chatAboutPhoto(photoId) {
        // Redirect to chat with photo reference
        window.location.href = `/ai_chat?photo_ref=${photoId}`;
    }

    function deletePhoto(photoId) {
        if (confirm('Are you sure you want to delete this photo? This action cannot be undone.')) {
            showLoading();

            fetch(`/delete_photo/${photoId}`, {
                method: 'DELETE'
            })
            .then(response => response.json())
            .then(data => {
                hideLoading();

                if (data.success) {
                    // Remove the photo card from the gallery
                    const photoCard = document.querySelector(`[data-photo-id="${photoId}"]`);
                    if (photoCard) {
                        photoCard.style.opacity = '0';
                        setTimeout(() => {
                            photoCard.remove();

                            // Check if gallery is now empty
                            const remainingPhotos = document.querySelectorAll('.photo-card');
                            if (remainingPhotos.length === 0) {
                                location.reload(); // Reload to show empty state
                            }
                        }, 300);
                    }

                    showNotification('Photo deleted successfully', 'success');
                } else {
                    showNotification(data.error || 'Failed to delete photo', 'error');
                }
            })
            .catch(error => {
                hideLoading();
                console.error('Error deleting photo:', error);
                showNotification('Failed to delete photo', 'error');
            });
        }
    }

    function showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
            ${message}
        `;

        // Add to page
        document.body.appendChild(notification);

        // Show notification
        setTimeout(() => {
            notification.classList.add('show');
        }, 100);

        // Hide and remove notification
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, 3000);
    }

    // Make functions globally available for onclick handlers
    window.analyzePhoto = analyzePhoto;
    window.chatAboutPhoto = chatAboutPhoto;
    window.deletePhoto = deletePhoto;
    window.viewPhotoDiagnosis = viewPhotoDiagnosis;
});

// Image lazy loading
document.addEventListener('DOMContentLoaded', function() {
    const images = document.querySelectorAll('img[loading="lazy"]');

    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.src; // Trigger load
                observer.unobserve(img);
            }
        });
    });

    images.forEach(img => imageObserver.observe(img));
});

// Search and filter functionality
function initializePhotoFilters() {
    const searchInput = document.getElementById('photoSearch');
    const statusFilter = document.getElementById('statusFilter');
    const plantFilter = document.getElementById('plantFilter');

    if (searchInput) {
        searchInput.addEventListener('input', filterPhotos);
    }
    if (statusFilter) {
        statusFilter.addEventListener('change', filterPhotos);
    }
    if (plantFilter) {
        plantFilter.addEventListener('change', filterPhotos);
    }
}

function filterPhotos() {
    const searchTerm = document.getElementById('photoSearch')?.value.toLowerCase() || '';
    const statusFilter = document.getElementById('statusFilter')?.value || 'all';
    const plantFilter = document.getElementById('plantFilter')?.value || 'all';

    const photoCards = document.querySelectorAll('.photo-card');

    photoCards.forEach(card => {
        let show = true;

        // Search filter
        if (searchTerm) {
            const searchableText = card.textContent.toLowerCase();
            show = show && searchableText.includes(searchTerm);
        }

        // Status filter
        if (statusFilter !== 'all') {
            const cardStatus = card.querySelector('.status-badge').textContent.toLowerCase();
            show = show && cardStatus.includes(statusFilter);
        }

        // Plant filter
        if (plantFilter !== 'all') {
            const plantName = card.querySelector('h4').textContent;
            show = show && plantName.includes(plantFilter);
        }

        card.style.display = show ? 'block' : 'none';
    });
}

// Initialize filters if they exist
document.addEventListener('DOMContentLoaded', initializePhotoFilters);