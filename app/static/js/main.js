// Main JavaScript file for POP application

// Auto-dismiss alerts after 5 seconds
document.addEventListener('DOMContentLoaded', function() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            // Check if bootstrap is available
            if (typeof bootstrap !== 'undefined') {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            } else {
                // Fallback if bootstrap is not loaded
                alert.style.opacity = '0';
                setTimeout(function() {
                    alert.style.display = 'none';
                }, 300);
            }
        }, 5000);
    });
});

// Password visibility toggle (if needed)
function togglePasswordVisibility(fieldId) {
    const field = document.getElementById(fieldId);
    if (field) {
        if (field.type === 'password') {
            field.type = 'text';
        } else {
            field.type = 'password';
        }
    }
}

// Form validation
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    }
}

// Confirmation dialog for destructive actions
function confirmAction(message) {
    return confirm(message || 'Êtes-vous sûr de vouloir effectuer cette action?');
}
