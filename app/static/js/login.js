// Navbar Toggle for Mobile
const navbarToggler = document.querySelector('.navbar-toggler');
const navbarMenu = document.querySelector('.navbar-menu');
navbarToggler.addEventListener('click', () => {
  navbarMenu.classList.toggle('active');
});

// Initialize Bootstrap Tooltips
document.addEventListener('DOMContentLoaded', () => {
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });
});

// Get references to form and loading elements
const loginForm = document.querySelector('.login-form');
const loginBtn = document.getElementById('login-btn');
const loginLoading = document.getElementById('login-loading');
const errorMessage = document.querySelector('.flash-messages');

// Handle Form Submission for Loading Indicator and Prevent Multiple Submissions
loginForm.addEventListener('submit', (event) => {
  // Show loading spinner
  loginLoading.style.display = 'flex';
  // Disable the submit button to prevent multiple submissions
  loginBtn.disabled = true;
  loginBtn.textContent = 'Logging in...';
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

// Example: Display notification based on session messages (server-side)
// Since external JS cannot contain Jinja2 templating, pass messages via a global variable
// Add the following script in the HTML before including room_selector.js:
// <script>
//   window.flashed_messages = {{ get_flashed_messages() | tojson }};
// </script>
// Then, in this JS file, handle the flashed_messages
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
