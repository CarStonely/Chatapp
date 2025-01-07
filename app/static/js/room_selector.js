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

// Get references to modal elements
const openModalBtn = document.getElementById('open-modal-btn');
const modal = document.getElementById('create-room-modal');
const closeModalBtn = document.getElementById('close-modal');
const createRoomForm = document.getElementById('create-room-form');
const errorMessage = document.getElementById('error-message');

// Function to open the modal
function openModal() {
  modal.classList.remove('hidden');
  modal.setAttribute('aria-hidden', 'false');
}

// Function to close the modal
function closeModalFunc() {
  modal.classList.add('hidden');
  modal.setAttribute('aria-hidden', 'true');
  // Clear any previous error messages
  errorMessage.style.display = 'none';
  errorMessage.textContent = '';
  // Reset the form
  createRoomForm.reset();
}

// Open the modal when the "Create Room" button is clicked
openModalBtn.addEventListener('click', openModal);

// Close the modal when the "x" button is clicked
closeModalBtn.addEventListener('click', closeModalFunc);

// Close the modal when clicking outside the modal content
window.addEventListener('click', (event) => {
  if (event.target === modal) {
    closeModalFunc();
  }
});

// Handle form submission for creating a room (Optional: Implement AJAX)
createRoomForm.addEventListener('submit', (event) => {
  // Optional: Implement AJAX form submission for better UX
  // Prevent default form submission to handle via JavaScript
  // Uncomment the following lines if using AJAX
  /*
  event.preventDefault();
  const formData = new FormData(createRoomForm);
  fetch('{{ url_for("rooms.create_room") }}', {
    method: 'POST',
    body: formData,
    headers: {
      'X-Requested-With': 'XMLHttpRequest' // To identify AJAX requests server-side
    }
  })
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      // Room created successfully, redirect or update the room list
      window.location.href = `/chat/${encodeURIComponent(data.room)}`;
    } else {
      // Display error message
      errorMessage.textContent = data.error || 'An error occurred.';
      errorMessage.style.display = 'block';
    }
  })
  .catch(error => {
    console.error('Error creating room:', error);
    errorMessage.textContent = 'An unexpected error occurred.';
    errorMessage.style.display = 'block';
  });
  */
  // If not using AJAX, the form will submit normally
  // Ensure server-side handles errors and redirects appropriately
});

// Function to show notifications
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
  window.flashed_messages.forEach(message => {
    showNotification(message, 'success'); // Adjust type as needed
  });
}

// Function to filter rooms based on search query
function filterRooms(query) {
  const lowerCaseQuery = query.toLowerCase();
  const roomList = document.getElementById('room-list');
  const roomListItems = roomList.querySelectorAll('li');
  let visibleCount = 0;

  roomListItems.forEach(item => {
    const roomLink = item.querySelector('.room-link');
    if (roomLink) {
      const roomName = roomLink.textContent.toLowerCase();
      if (roomName.includes(lowerCaseQuery)) {
        item.style.display = 'block';
        visibleCount++;
      } else {
        item.style.display = 'none';
      }
    }
  });

  // If no rooms match the search, display a message
  let noRoomsMessage = document.getElementById('no-rooms-message');
  if (visibleCount === 0) {
    if (!noRoomsMessage) {
      noRoomsMessage = document.createElement('li');
      noRoomsMessage.id = 'no-rooms-message';
      noRoomsMessage.textContent = 'No rooms found.';
      noRoomsMessage.style.backgroundColor = 'rgba(255, 255, 255, 0.2)';
      noRoomsMessage.style.padding = '0.75rem 1rem';
      noRoomsMessage.style.borderRadius = '5px';
      roomList.appendChild(noRoomsMessage);
    }
  } else {
    if (noRoomsMessage) {
      noRoomsMessage.remove();
    }
  }
}

// Get references to search input and room list
const roomSearchInput = document.getElementById('room-search');

// Add event listener to search input
roomSearchInput.addEventListener('input', (event) => {
  const query = event.target.value;
  filterRooms(query);
});
