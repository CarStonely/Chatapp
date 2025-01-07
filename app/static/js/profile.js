// Navbar Toggle for Mobile Devices
const navbarToggler = document.querySelector('.navbar-toggler');
const navbarMenu = document.querySelector('.navbar-menu');
navbarToggler.addEventListener('click', () => {
  navbarMenu.classList.toggle('active');
});

// Initialize Bootstrap Tooltips (if any)
document.addEventListener('DOMContentLoaded', () => {
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });
});

// Get references to form and loading elements
const profileForm = document.querySelector('form');
const updateProfileBtn = document.getElementById('update-profile-btn');
const profileLoading = document.getElementById('profile-loading');

// Handle Form Submission for Loading Indicator and Prevent Multiple Submissions
profileForm.addEventListener('submit', (event) => {
  // Show loading spinner
  profileLoading.style.display = 'flex';
  // Disable the submit button to prevent multiple submissions
  updateProfileBtn.disabled = true;
  updateProfileBtn.textContent = 'Updating...';
});

// Function to show notifications (if using AJAX or additional client-side notifications)
function showNotification(message, type = 'info') {
  const notification = document.createElement('div');
  notification.classList.add('notification');
  notification.style.backgroundColor = type === 'info' ? '#17a2b8' :
                                     type === 'success' ? '#28a745' :
                                     type === 'warning' ? '#ffc107' :
                                     '#dc3545';
  notification.style.color = '#fff';
  notification.textContent = message;
  document.body.appendChild(notification);
  setTimeout(() => {
    notification.remove();
  }, 5000);
}

// Display Notifications Based on Flashed Messages
if (typeof window.flashed_messages !== 'undefined' && Array.isArray(window.flashed_messages)) {
  window.flashed_messages.forEach(([category, message]) => {
    // Adjust type based on category
    let type = 'info';
    if (category === 'success') type = 'success';
    else if (category === 'error') type = 'error';
    else if (category === 'warning') type = 'warning';
    else if (category === 'info') type = 'info';
    showNotification(message, type);
  });
}
