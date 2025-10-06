// Main JavaScript functionality for the expense tracker

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Format currency inputs
    const currencyInputs = document.querySelectorAll('input[type="number"][step="0.01"]');
    currencyInputs.forEach(function(input) {
        input.addEventListener('blur', function() {
            if (this.value) {
                this.value = parseFloat(this.value).toFixed(2);
            }
        });
    });

    // Confirm delete actions
    const deleteButtons = document.querySelectorAll('[onclick*="confirm"]');
    deleteButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this expense?')) {
                e.preventDefault();
                return false;
            }
        });
    });

    // Add loading state to forms
    const forms = document.querySelectorAll('form');
    forms.forEach(function(form) {
        form.addEventListener('submit', function() {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
            }
        });
    });

    // Category color indicators
    addCategoryColorIndicators();

    // Chart animations
    if (typeof Chart !== 'undefined') {
        Chart.defaults.animation.duration = 1000;
        Chart.defaults.animation.easing = 'easeInOutQuart';
    }
});

// Add color indicators for categories
function addCategoryColorIndicators() {
    const categoryColors = {
        'Food & Dining': '#FF6B6B',
        'Transportation': '#4ECDC4',
        'Shopping': '#45B7D1',
        'Entertainment': '#96CEB4',
        'Bills & Utilities': '#FECA57',
        'Healthcare': '#FF9FF3',
        'Education': '#54A0FF',
        'Travel': '#5F27CD',
        'Other': '#00D2D3'
    };

    const categoryBadges = document.querySelectorAll('.badge');
    categoryBadges.forEach(function(badge) {
        const category = badge.textContent.trim();
        if (categoryColors[category]) {
            badge.style.backgroundColor = categoryColors[category];
            badge.style.borderColor = categoryColors[category];
        }
    });
}

// Utility function to format currency
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

// Export data functionality (can be extended)
function exportData(format) {
    // This can be extended to export data in different formats
    console.log('Exporting data in format:', format);
    // Implementation would depend on requirements
}

// Theme toggle functionality (for future enhancement)
function toggleTheme() {
    document.body.classList.toggle('dark-theme');
    localStorage.setItem('theme', document.body.classList.contains('dark-theme') ? 'dark' : 'light');
}

// Load saved theme preference
function loadThemePreference() {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        document.body.classList.add('dark-theme');
    }
}

// Initialize theme on page load
loadThemePreference();
