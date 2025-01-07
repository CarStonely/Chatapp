// view_profile.js

document.addEventListener('DOMContentLoaded', () => {
    // Navbar Toggle for Mobile Devices
    const navbarToggler = document.querySelector('.navbar-toggler');
    const navbarMenu = document.querySelector('.navbar-menu');
    if (navbarToggler) {
      navbarToggler.addEventListener('click', () => {
        navbarMenu.classList.toggle('active');
      });
    }
  
    // Initialize Bootstrap Tooltips (if any)
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
      return new bootstrap.Tooltip(tooltipTriggerEl);
    });
  
    // Get references to action buttons and loading elements
    const actionButtons = document.querySelectorAll('.action-buttons a');
    const profileLoading = document.getElementById('profile-loading');
  
    // Handle Action Button Clicks for Loading Indicator
    actionButtons.forEach(button => {
      button.addEventListener('click', (event) => {
        // Show loading spinner
        profileLoading.style.display = 'flex';
        // Optionally, disable the button to prevent multiple clicks
        button.classList.add('disabled');
      });
    });
  
    // Function to show notifications
    function showNotification(message, type = 'info') {
      const notification = document.createElement('div');
      notification.classList.add('notification');
      // Set background color based on type
      switch(type) {
        case 'success':
          notification.style.backgroundColor = '#28a745';
          notification.style.color = '#fff';
          break;
        case 'error':
          notification.style.backgroundColor = '#dc3545';
          notification.style.color = '#fff';
          break;
        case 'warning':
          notification.style.backgroundColor = '#ffc107';
          notification.style.color = '#212529';
          break;
        case 'info':
        default:
          notification.style.backgroundColor = '#17a2b8';
          notification.style.color = '#fff';
          break;
      }
      notification.textContent = message;
      document.body.appendChild(notification);
      // Trigger reflow for animation
      void notification.offsetWidth;
      // Add animation class
      notification.classList.add('show');
      // Remove after 5 seconds
      setTimeout(() => {
        notification.classList.remove('show');
        // Remove from DOM after transition
        notification.addEventListener('transitionend', () => {
          notification.remove();
        });
      }, 5000);
    }
  
    // Display notifications based on flashed messages
    if (window.flashedMessages && Array.isArray(window.flashedMessages)) {
      window.flashedMessages.forEach(([category, message]) => {
        showNotification(message, category);
      });
    }
  });
  