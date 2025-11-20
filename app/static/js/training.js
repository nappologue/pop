/**
 * Training Player JavaScript
 * Handles slideshow navigation, progress tracking, and auto-save
 */

class TrainingPlayer {
    constructor(config) {
        this.trainingId = config.trainingId;
        this.currentSlideIndex = config.currentSlideIndex || 0;
        this.totalSlides = config.totalSlides;
        this.completedSlides = new Set(config.completedSlides || []);
        
        this.initializeElements();
        this.attachEventListeners();
        this.loadSlide(this.currentSlideIndex);
        this.updateUI();
    }
    
    initializeElements() {
        this.slideDisplay = document.getElementById('slideDisplay');
        this.prevButton = document.getElementById('prevButton');
        this.nextButton = document.getElementById('nextButton');
        this.currentSlideSpan = document.getElementById('currentSlide');
        this.progressBar = document.getElementById('topProgressBar');
        this.progressText = document.getElementById('progressText');
    }
    
    attachEventListeners() {
        this.prevButton.addEventListener('click', () => this.previousSlide());
        this.nextButton.addEventListener('click', () => this.nextSlide());
        
        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowLeft') {
                this.previousSlide();
            } else if (e.key === 'ArrowRight') {
                this.nextSlide();
            }
        });
    }
    
    loadSlide(index) {
        // Show loading spinner
        this.slideDisplay.innerHTML = `
            <div class="text-center py-5">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Chargement...</span>
                </div>
            </div>
        `;
        
        // Fetch slide content
        fetch(`/trainings/${this.trainingId}/slides/${index}`, {
            headers: {
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.slideDisplay.innerHTML = data.slide.html;
                this.completedSlides.add(index);
                this.updateUI();
                
                // Auto-save progress (debounced)
                this.saveProgress(index);
            } else {
                this.slideDisplay.innerHTML = `
                    <div class="alert alert-danger">
                        <i class="bi bi-exclamation-triangle"></i>
                        Erreur lors du chargement de la diapositive: ${data.error}
                    </div>
                `;
            }
        })
        .catch(error => {
            console.error('Error loading slide:', error);
            this.slideDisplay.innerHTML = `
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle"></i>
                    Erreur lors du chargement de la diapositive.
                </div>
            `;
        });
    }
    
    saveProgress(slideIndex) {
        // Debounced save to avoid too many requests
        clearTimeout(this.saveTimeout);
        this.saveTimeout = setTimeout(() => {
            fetch(`/trainings/${this.trainingId}/progress`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
                },
                body: JSON.stringify({
                    slide_index: slideIndex
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    console.log('Progress saved');
                    
                    // Check if training is complete
                    if (data.progress.status === 'completed') {
                        this.showCompletionMessage();
                    }
                }
            })
            .catch(error => {
                console.error('Error saving progress:', error);
            });
        }, 500);
    }
    
    previousSlide() {
        if (this.currentSlideIndex > 0) {
            this.currentSlideIndex--;
            this.loadSlide(this.currentSlideIndex);
        }
    }
    
    nextSlide() {
        if (this.currentSlideIndex < this.totalSlides - 1) {
            this.currentSlideIndex++;
            this.loadSlide(this.currentSlideIndex);
        } else {
            // Last slide - show completion
            this.completeTraining();
        }
    }
    
    updateUI() {
        // Update slide counter
        this.currentSlideSpan.textContent = this.currentSlideIndex + 1;
        
        // Update navigation buttons
        this.prevButton.disabled = this.currentSlideIndex === 0;
        this.nextButton.disabled = false;
        
        if (this.currentSlideIndex === this.totalSlides - 1) {
            this.nextButton.innerHTML = '<i class="bi bi-check-circle"></i> Terminer';
        } else {
            this.nextButton.innerHTML = 'Suivant <i class="bi bi-arrow-right"></i>';
        }
        
        // Update progress bar
        const progress = (this.completedSlides.size / this.totalSlides) * 100;
        this.progressBar.style.width = progress + '%';
        this.progressBar.setAttribute('aria-valuenow', progress);
        
        // Update progress text
        this.progressText.textContent = `${this.completedSlides.size} / ${this.totalSlides} diapositives complétées`;
    }
    
    completeTraining() {
        if (confirm('Voulez-vous marquer cette formation comme terminée?')) {
            fetch(`/trainings/${this.trainingId}/complete`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.showCompletionMessage();
                } else {
                    alert('Erreur: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error completing training:', error);
                alert('Erreur lors de la complétion de la formation');
            });
        }
    }
    
    showCompletionMessage() {
        this.slideDisplay.innerHTML = `
            <div class="text-center py-5">
                <i class="bi bi-check-circle-fill text-success" style="font-size: 5rem;"></i>
                <h2 class="mt-4">Félicitations!</h2>
                <p class="lead">Vous avez complété cette formation avec succès.</p>
                <div class="mt-4">
                    <a href="/trainings" class="btn btn-primary">
                        <i class="bi bi-arrow-left"></i> Retour aux formations
                    </a>
                </div>
            </div>
        `;
        
        // Disable navigation
        this.prevButton.disabled = true;
        this.nextButton.disabled = true;
    }
}

// Export for global use
window.TrainingPlayer = TrainingPlayer;
