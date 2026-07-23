/**
 * Blood Donor Network Main JavaScript
 * Handles AJAX notifications and global interactions.
 */

document.addEventListener("DOMContentLoaded", function() {
    
    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-important)');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Handle Notifications Dropdown
    const notifDropdown = document.getElementById('notifDropdown');
    const notifList = document.getElementById('notif-list');
    const notifBadge = document.getElementById('notif-badge');

    if (notifDropdown && notifList) {
        notifDropdown.addEventListener('show.bs.dropdown', function () {
            // Fetch latest notifications via AJAX
            fetch('/notifications/api/latest/')
                .then(response => response.json())
                .then(data => {
                    notifList.innerHTML = ''; // Clear loading
                    
                    if (data.notifications.length === 0) {
                        notifList.innerHTML = '<div class="p-3 text-center text-muted small">No new notifications</div>';
                        return;
                    }
                    
                    data.notifications.forEach(notif => {
                        let icon = '<i class="fa-solid fa-circle-info text-primary"></i>';
                        if (notif.type === 'emergency') {
                            icon = '<i class="fa-solid fa-triangle-exclamation text-danger"></i>';
                        } else if (notif.type === 'request_accepted') {
                            icon = '<i class="fa-solid fa-handshake-angle text-success"></i>';
                        }

                        const itemHtml = `
                            <a class="dropdown-item d-flex align-items-center py-2" href="/notifications/read/${notif.id}/">
                                <div class="me-3 fs-5">${icon}</div>
                                <div>
                                    <h6 class="mb-0 text-dark small fw-bold text-wrap" style="width: 200px;">${notif.title}</h6>
                                    <div class="text-muted small">${notif.created_at}</div>
                                </div>
                            </a>
                        `;
                        notifList.innerHTML += itemHtml;
                    });
                })
                .catch(error => {
                    notifList.innerHTML = '<div class="p-3 text-center text-danger small">Error loading notifications</div>';
                });
        });
    }

    // Optional: Set up polling for unread count every 30 seconds
    if (notifBadge) {
        setInterval(function() {
            fetch('/notifications/api/unread-count/')
                .then(response => response.json())
                .then(data => {
                    if (data.count > 0) {
                        notifBadge.textContent = data.count;
                        notifBadge.classList.remove('d-none');
                    } else {
                        notifBadge.classList.add('d-none');
                    }
                });
        }, 30000);
    }
});
