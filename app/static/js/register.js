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
const registerForm = document.querySelector('.login-form');
const registerBtn = document.getElementById('register-btn');
const registerLoading = document.getElementById('register-loading');

// Handle Form Submission for Loading Indicator and Prevent Multiple Submissions
registerForm.addEventListener('submit', function(event) {
  event.preventDefault(); // Prevent default form submission

  // Show loading spinner and disable submit button
  registerLoading.style.display = 'flex';
  registerBtn.disabled = true;
  registerBtn.textContent = 'Registering...';

  // Gather form data
  const formData = new FormData(registerForm);

  // Send AJAX request
  fetch(window.registrationURL, {
    method: 'POST',
    body: formData,
    headers: {
      'X-Requested-With': 'XMLHttpRequest' // To identify AJAX requests server-side
    }
  })
  .then(response => {
    if (!response.ok) {
      return response.json().then(errorData => {
        throw new Error(errorData.error || 'An error occurred during registration.');
      });
    }
    return response.json();
  })
  .then(data => {
    // Hide loading spinner and enable submit button
    registerLoading.style.display = 'none';
    registerBtn.disabled = false;
    registerBtn.textContent = 'Register';
  
    if (data.success) {
      showNotification(data.message || 'Registration successful!', 'success');
      setTimeout(() => {
        window.location.href = '{{ url_for("auth.login") }}';
      }, 2000);
    } else {
      showNotification(data.error || 'Registration failed. Please try again.', 'error');
    }
  })
  .catch(error => {
    console.error('Error:', error);
    registerLoading.style.display = 'none';
    registerBtn.disabled = false;
    registerBtn.textContent = 'Register';
    showNotification(error.message, 'error');
  });
});

/**
 * Shows a notification to the user.
 * @param {string} message - The message to display.
 * @param {string} type - The type of notification ('info', 'success', 'warning', 'error').
 */
function showNotification(message, type = 'info') {
  const notification = document.createElement('div');
  notification.classList.add('notification');
  
  // Set background color based on the type
  notification.style.backgroundColor = type === 'info' ? '#17a2b8' :
                                     type === 'success' ? '#28a745' :
                                     type === 'warning' ? '#ffc107' :
                                     '#dc3545';
  notification.style.color = '#fff';
  notification.textContent = message;
  document.body.appendChild(notification);
  
  // Remove the notification after 5 seconds
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
