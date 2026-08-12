/**
 * Blood Donor Network Main JavaScript
 * Auto-dismiss notifications and messages.
 */

document.addEventListener("DOMContentLoaded", function() {
    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-important)');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            try {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            } catch (e) {}
        }, 5000);
    });
});
