/**
 * Quiz Player JavaScript
 * Handles quiz taking, timer, answer selection, and submission
 */

class QuizPlayer {
    constructor(config) {
        this.quizId = config.quizId;
        this.attemptId = config.attemptId;
        this.timeLimit = config.timeLimit; // in minutes
        this.questions = config.questions;
        this.savedAnswers = config.savedAnswers || {};
        this.currentQuestionIndex = 0;
        this.answers = {};
        
        // Load saved answers
        this.loadSavedAnswers();
        
        this.initializeElements();
        this.renderQuestion(this.currentQuestionIndex);
        this.renderQuestionNavigator();
        this.attachEventListeners();
        
        if (this.timeLimit) {
            this.startTimer();
        }
    }
    
    initializeElements() {
        this.questionDisplay = document.getElementById('questionDisplay');
        this.prevButton = document.getElementById('prevQuestionBtn');
        this.nextButton = document.getElementById('nextQuestionBtn');
        this.submitSection = document.getElementById('submitSection');
        this.submitButton = document.getElementById('submitQuizBtn');
        this.currentQuestionSpan = document.getElementById('currentQuestion');
        this.progressBar = document.getElementById('quizProgress');
        this.questionNavigator = document.getElementById('questionNavigator');
    }
    
    loadSavedAnswers() {
        if (this.savedAnswers) {
            for (const [questionId, answer] of Object.entries(this.savedAnswers)) {
                if (questionId !== '_quiz_instance') {
                    this.answers[questionId] = answer;
                }
            }
        }
    }
    
    attachEventListeners() {
        this.prevButton.addEventListener('click', () => this.previousQuestion());
        this.nextButton.addEventListener('click', () => this.nextQuestion());
        this.submitButton.addEventListener('click', () => this.showSubmitModal());
        
        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowLeft' && !this.prevButton.disabled) {
                this.previousQuestion();
            } else if (e.key === 'ArrowRight' && this.currentQuestionIndex < this.questions.length - 1) {
                this.nextQuestion();
            }
        });
    }
    
    renderQuestion(index) {
        const question = this.questions[index];
        
        let answersHTML = '';
        const inputType = question.type === 'single_choice' ? 'radio' : 'checkbox';
        const savedAnswer = this.answers[question.id];
        
        question.answers.forEach((answer, answerIndex) => {
            const isChecked = this.isAnswerSelected(question.id, answerIndex, question.type);
            
            answersHTML += `
                <div class="answer-option ${isChecked ? 'selected' : ''}" data-answer-index="${answerIndex}">
                    <label class="w-100">
                        <input type="${inputType}" 
                               name="question_${question.id}" 
                               value="${answerIndex}"
                               ${isChecked ? 'checked' : ''}
                               class="me-2">
                        ${answer.text}
                    </label>
                </div>
            `;
        });
        
        this.questionDisplay.innerHTML = `
            <div class="question-text">${index + 1}. ${question.text}</div>
            <div class="answers-container">
                ${answersHTML}
            </div>
            <div class="mt-3">
                <small class="text-muted">
                    <i class="bi bi-star"></i> ${question.points} point(s)
                </small>
            </div>
        `;
        
        // Attach answer selection listeners
        this.attachAnswerListeners(question);
        
        // Update UI
        this.updateUI();
    }
    
    isAnswerSelected(questionId, answerIndex, questionType) {
        const savedAnswer = this.answers[questionId];
        if (!savedAnswer) return false;
        
        if (questionType === 'single_choice') {
            return savedAnswer === answerIndex;
        } else {
            return Array.isArray(savedAnswer) && savedAnswer.includes(answerIndex);
        }
    }
    
    attachAnswerListeners(question) {
        const answerOptions = document.querySelectorAll('.answer-option');
        
        answerOptions.forEach(option => {
            option.addEventListener('click', function(e) {
                const input = this.querySelector('input');
                const answerIndex = parseInt(this.dataset.answerIndex);
                
                if (input.type === 'radio') {
                    // Single choice - deselect all others
                    answerOptions.forEach(opt => opt.classList.remove('selected'));
                    this.classList.add('selected');
                    input.checked = true;
                } else {
                    // Multiple choice - toggle
                    this.classList.toggle('selected');
                    input.checked = !input.checked;
                }
                
                // Prevent double-triggering from label click
                if (e.target.tagName !== 'INPUT') {
                    e.preventDefault();
                }
            });
            
            // Also handle input change
            const input = option.querySelector('input');
            input.addEventListener('change', function() {
                if (this.type === 'radio') {
                    answerOptions.forEach(opt => opt.classList.remove('selected'));
                    option.classList.add('selected');
                } else {
                    if (this.checked) {
                        option.classList.add('selected');
                    } else {
                        option.classList.remove('selected');
                    }
                }
            });
        });
        
        // Save answers when they change
        const inputs = document.querySelectorAll('.answer-option input');
        inputs.forEach(input => {
            input.addEventListener('change', () => {
                this.saveCurrentAnswer();
            });
        });
    }
    
    saveCurrentAnswer() {
        const question = this.questions[this.currentQuestionIndex];
        const inputs = document.querySelectorAll('.answer-option input');
        
        if (question.type === 'single_choice') {
            const selected = document.querySelector('.answer-option input:checked');
            this.answers[question.id] = selected ? parseInt(selected.value) : null;
        } else {
            const selected = Array.from(inputs)
                .filter(input => input.checked)
                .map(input => parseInt(input.value));
            this.answers[question.id] = selected;
        }
        
        // Auto-save to server (debounced)
        this.autoSave();
        
        // Update navigator
        this.updateQuestionNavigator();
    }
    
    autoSave() {
        clearTimeout(this.saveTimeout);
        this.saveTimeout = setTimeout(() => {
            const question = this.questions[this.currentQuestionIndex];
            const answer = this.answers[question.id];
            
            fetch(`/quiz/${this.quizId}/attempt/${this.attemptId}/answer`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
                },
                body: JSON.stringify({
                    question_id: question.id,
                    answer: answer
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    console.log('Answer saved');
                }
            })
            .catch(error => {
                console.error('Error saving answer:', error);
            });
        }, 1000);
    }
    
    previousQuestion() {
        if (this.currentQuestionIndex > 0) {
            this.currentQuestionIndex--;
            this.renderQuestion(this.currentQuestionIndex);
        }
    }
    
    nextQuestion() {
        if (this.currentQuestionIndex < this.questions.length - 1) {
            this.currentQuestionIndex++;
            this.renderQuestion(this.currentQuestionIndex);
        }
    }
    
    goToQuestion(index) {
        this.currentQuestionIndex = index;
        this.renderQuestion(this.currentQuestionIndex);
    }
    
    updateUI() {
        // Update question counter
        this.currentQuestionSpan.textContent = this.currentQuestionIndex + 1;
        
        // Update navigation buttons
        this.prevButton.disabled = this.currentQuestionIndex === 0;
        this.nextButton.style.display = this.currentQuestionIndex === this.questions.length - 1 ? 'none' : 'inline-block';
        this.submitSection.style.display = this.currentQuestionIndex === this.questions.length - 1 ? 'block' : 'none';
        
        // Update progress bar
        const answered = Object.keys(this.answers).length;
        const progress = (answered / this.questions.length) * 100;
        this.progressBar.style.width = progress + '%';
        this.progressBar.setAttribute('aria-valuenow', progress);
    }
    
    renderQuestionNavigator() {
        let html = '';
        this.questions.forEach((question, index) => {
            const isAnswered = this.answers[question.id] !== undefined && this.answers[question.id] !== null;
            const isCurrent = index === this.currentQuestionIndex;
            const btnClass = isCurrent ? 'current' : (isAnswered ? 'answered' : 'unanswered');
            
            html += `
                <button type="button" 
                        class="question-nav-btn ${btnClass}" 
                        data-index="${index}"
                        onclick="quizPlayer.goToQuestion(${index})">
                    ${index + 1}
                </button>
            `;
        });
        
        this.questionNavigator.innerHTML = html;
    }
    
    updateQuestionNavigator() {
        const buttons = this.questionNavigator.querySelectorAll('.question-nav-btn');
        buttons.forEach((button, index) => {
            const question = this.questions[index];
            const isAnswered = this.answers[question.id] !== undefined && this.answers[question.id] !== null;
            const isCurrent = index === this.currentQuestionIndex;
            
            button.className = 'question-nav-btn';
            if (isCurrent) {
                button.classList.add('current');
            } else if (isAnswered) {
                button.classList.add('answered');
            } else {
                button.classList.add('unanswered');
            }
        });
        
        // Update progress
        this.updateUI();
    }
    
    showSubmitModal() {
        const unanswered = this.questions.length - Object.keys(this.answers).length;
        
        if (unanswered > 0) {
            document.getElementById('unansweredWarning').style.display = 'block';
            document.getElementById('unansweredCount').textContent = unanswered;
        } else {
            document.getElementById('unansweredWarning').style.display = 'none';
        }
        
        const modal = new bootstrap.Modal(document.getElementById('submitModal'));
        modal.show();
        
        // Attach submit handler
        document.getElementById('confirmSubmitBtn').onclick = () => {
            this.submitQuiz();
        };
    }
    
    submitQuiz() {
        // Disable submit button
        const submitBtn = document.getElementById('confirmSubmitBtn');
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Envoi...';
        
        fetch(`/quiz/${this.quizId}/attempt/${this.attemptId}/complete`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.location.href = data.redirect_url;
            } else {
                alert('Erreur: ' + data.error);
                submitBtn.disabled = false;
                submitBtn.innerHTML = 'Soumettre';
            }
        })
        .catch(error => {
            console.error('Error submitting quiz:', error);
            alert('Erreur lors de la soumission du quiz');
            submitBtn.disabled = false;
            submitBtn.innerHTML = 'Soumettre';
        });
    }
    
    startTimer() {
        let timeRemaining = this.timeLimit * 60; // Convert to seconds
        const timerDisplay = document.getElementById('timeRemaining');
        const timerElement = document.getElementById('quizTimer');
        
        this.timerInterval = setInterval(() => {
            timeRemaining--;
            
            const minutes = Math.floor(timeRemaining / 60);
            const seconds = timeRemaining % 60;
            timerDisplay.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
            
            // Warning at 5 minutes
            if (timeRemaining === 300) {
                timerElement.classList.add('warning');
            }
            
            // Danger at 1 minute
            if (timeRemaining === 60) {
                timerElement.classList.remove('warning');
                timerElement.classList.add('danger');
            }
            
            // Time's up
            if (timeRemaining <= 0) {
                clearInterval(this.timerInterval);
                alert('Le temps est écoulé! Le quiz sera soumis automatiquement.');
                this.submitQuiz();
            }
        }, 1000);
    }
}

// Export for global use
window.QuizPlayer = QuizPlayer;
