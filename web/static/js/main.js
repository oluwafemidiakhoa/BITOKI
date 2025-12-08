// Main JavaScript for BITOKI Platform

// Global variables
let priceUpdateInterval = null;

// Initialize on page load
$(document).ready(function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Add fade-in animation to cards
    $('.card').addClass('fade-in');

    // Start price updates if on trading page
    if (window.location.pathname.includes('/trade')) {
        startPriceUpdates();
    }
});

// Price update functions
function startPriceUpdates() {
    updatePrices();
    priceUpdateInterval = setInterval(updatePrices, 10000); // Update every 10 seconds
}

function stopPriceUpdates() {
    if (priceUpdateInterval) {
        clearInterval(priceUpdateInterval);
    }
}

function updatePrices() {
    const currencies = ['BTC', 'ETH', 'SOL', 'USDT'];

    currencies.forEach(currency => {
        $.get(`/api/trade/price/${currency}`, function(data) {
            if (data.success) {
                $(`.price-${currency}`).text('$' + data.price.toLocaleString());
            }
        }).fail(function() {
            console.log(`Failed to fetch ${currency} price`);
        });
    });
}

// Format number with commas
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

// Format currency
function formatCurrency(amount, currency = 'USD') {
    if (currency === 'USD') {
        return '$' + amount.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    } else {
        return amount.toFixed(6) + ' ' + currency;
    }
}

// Show loading spinner
function showLoading(element) {
    $(element).html('<div class="spinner"></div>');
}

// Hide loading spinner
function hideLoading(element) {
    $(element).find('.spinner').remove();
}

// Show toast notification
function showToast(message, type = 'info') {
    const bgClass = type === 'success' ? 'bg-success' :
                    type === 'error' ? 'bg-danger' :
                    type === 'warning' ? 'bg-warning' : 'bg-info';

    const toast = `
        <div class="toast align-items-center text-white ${bgClass} border-0" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;

    // Create toast container if it doesn't exist
    if ($('#toast-container').length === 0) {
        $('body').append('<div id="toast-container" class="position-fixed top-0 end-0 p-3" style="z-index: 11"></div>');
    }

    $('#toast-container').append(toast);
    const toastElement = $('#toast-container .toast').last()[0];
    const bsToast = new bootstrap.Toast(toastElement);
    bsToast.show();

    // Remove toast after it's hidden
    $(toastElement).on('hidden.bs.toast', function() {
        $(this).remove();
    });
}

// Confirm dialog
function confirmDialog(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// Copy to clipboard
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        showToast('Copied to clipboard!', 'success');
    }, function(err) {
        showToast('Failed to copy', 'error');
    });
}

// Format date
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

// Validate form
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form.checkValidity()) {
        form.classList.add('was-validated');
        return false;
    }
    return true;
}

// Generate random color for charts
function getRandomColor() {
    const letters = '0123456789ABCDEF';
    let color = '#';
    for (let i = 0; i < 6; i++) {
        color += letters[Math.floor(Math.random() * 16)];
    }
    return color;
}

// Calculate percentage change
function calculatePercentageChange(oldValue, newValue) {
    if (oldValue === 0) return 0;
    return ((newValue - oldValue) / oldValue) * 100;
}

// Format percentage
function formatPercentage(value, decimals = 2) {
    const sign = value >= 0 ? '+' : '';
    return sign + value.toFixed(decimals) + '%';
}

// Debounce function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// API error handler
function handleAPIError(error) {
    console.error('API Error:', error);

    let message = 'An error occurred. Please try again.';

    if (error.responseJSON && error.responseJSON.error) {
        message = error.responseJSON.error;
    } else if (error.statusText) {
        message = error.statusText;
    }

    showToast(message, 'error');
}

// Check if user is logged in (placeholder)
function isLoggedIn() {
    // Implement actual authentication check
    return true;
}

// Logout function (placeholder)
function logout() {
    confirmDialog('Are you sure you want to logout?', function() {
        // Implement actual logout
        window.location.href = '/';
    });
}

// Format crypto address (shorten)
function formatAddress(address) {
    if (address.length <= 10) return address;
    return address.substring(0, 6) + '...' + address.substring(address.length - 4);
}

// Check transaction status
function checkTransactionStatus(txId) {
    // Implement transaction status checking
    console.log('Checking status for:', txId);
}

// Refresh page data
function refreshData() {
    location.reload();
}

// Export data to CSV
function exportToCSV(data, filename) {
    const csv = convertToCSV(data);
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    window.URL.revokeObjectURL(url);
}

function convertToCSV(data) {
    const array = [Object.keys(data[0])].concat(data);
    return array.map(row => {
        return Object.values(row).map(value => {
            return typeof value === 'string' ? `"${value}"` : value;
        }).join(',');
    }).join('\n');
}

// Window cleanup
$(window).on('beforeunload', function() {
    stopPriceUpdates();
});

// Handle navbar active state
$(document).ready(function() {
    const currentPath = window.location.pathname;
    $('.navbar-nav .nav-link').each(function() {
        const href = $(this).attr('href');
        if (currentPath === href || (href !== '/' && currentPath.startsWith(href))) {
            $(this).addClass('active');
        } else {
            $(this).removeClass('active');
        }
    });
});

// Form validation helper
function addValidationFeedback(inputElement, isValid, message) {
    const feedbackDiv = $(inputElement).siblings('.invalid-feedback');

    if (!isValid) {
        $(inputElement).addClass('is-invalid');
        if (feedbackDiv.length === 0) {
            $(inputElement).after(`<div class="invalid-feedback">${message}</div>`);
        } else {
            feedbackDiv.text(message);
        }
    } else {
        $(inputElement).removeClass('is-invalid');
        feedbackDiv.remove();
    }
}

// Clear form validation
function clearValidation(formId) {
    $(`#${formId} .is-invalid`).removeClass('is-invalid');
    $(`#${formId} .invalid-feedback`).remove();
}

// Console log for debugging (disable in production)
const DEBUG = true;

function debugLog(message, data) {
    if (DEBUG) {
        console.log(`[DEBUG] ${message}`, data || '');
    }
}

// Initialize WebSocket for real-time updates (placeholder)
function initializeWebSocket() {
    // Implement WebSocket connection for real-time price updates
    debugLog('WebSocket initialization placeholder');
}

// Export functions for use in other scripts
window.BITOKI = {
    formatNumber,
    formatCurrency,
    showToast,
    confirmDialog,
    copyToClipboard,
    formatDate,
    validateForm,
    handleAPIError,
    formatAddress,
    exportToCSV,
    debugLog
};
