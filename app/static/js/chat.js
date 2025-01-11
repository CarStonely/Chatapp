// Navbar Toggle for Mobile
const navbarToggler = document.querySelector('.navbar-toggler');
const navbarMenu = document.querySelector('.navbar-menu');
if (navbarToggler && navbarMenu) {
  navbarToggler.addEventListener('click', () => {
    navbarMenu.classList.toggle('active');
  });
}

// Initialize Bootstrap Tooltips
document.addEventListener('DOMContentLoaded', () => {
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });
});

// Socket.IO Setup
const socket = io();
const currentUser = document.getElementById('current-username').value;
const room = document.getElementById('room').value;
const messagesContainer = document.getElementById('messages');
const typingIndicator = document.getElementById('typing-indicator');
const onlineUsersList = document.getElementById('online-users');
const messagesLoading = document.getElementById('messages-loading');
const onlineUsersLoading = document.getElementById('online-users-loading');

// Scroll to bottom function
function scrollToBottom() {
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

// Show loading indicators initially and handle initial scroll
window.addEventListener('load', () => {
  messagesLoading.style.display = 'flex';
  onlineUsersLoading.style.display = 'flex';
  
  // Simulate loading delay (remove in production)
  setTimeout(() => {
    messagesLoading.style.display = 'none';
    onlineUsersLoading.style.display = 'none';
    scrollToBottom(); // Ensure scrolling after loading
  }, 1000);
});

// Join the room
socket.emit('join', { room });

// Handle incoming messages
socket.on('message', (data) => {
  appendMessage(data, data.user === currentUser);
  scrollToBottom(); // Scroll after appending a new message
});

// Message Sending
const messageInput = document.getElementById('message');
const sendButton = document.getElementById('send');

function sendMessage() {
  const message = messageInput.value.trim();
  if (message) {
    socket.emit('message', { message, room });
    messageInput.value = ''; // Clear input without manually appending the message
  }
}

sendButton.addEventListener('click', sendMessage);
messageInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') {
    e.preventDefault();
    sendMessage();
  }
});

// ===== Image Upload Handling =====
const attachButton = document.getElementById('attach-button');
const imageUpload = document.getElementById('image-upload');

attachButton.addEventListener('click', (e) => {
  e.preventDefault();
  imageUpload.click();
});

imageUpload.addEventListener('change', async (e) => {
  const file = e.target.files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append('image', file);

  try {
    const response = await fetch('/upload_image', {
      method: 'POST',
      body: formData
    });
    const data = await response.json();

    if (data.success) {
      const imageUrl = data.image_url;
      const message = messageInput.value.trim();
      socket.emit('message', { 
        message: message, 
        room: room, 
        image_url: imageUrl 
      });
      messageInput.value = '';
      imageUpload.value = '';
    } else {
      console.error('Upload failed:', data.error);
    }
  } catch (error) {
    console.error('Error uploading image:', error);
  }
});
// ===== End Image Upload Handling =====

// Typing Indicator Logic
let typing = false;
let typingTimeout;

messageInput.addEventListener('input', () => {
  if (!typing) {
    typing = true;
    socket.emit('typing', { room });
  }
  clearTimeout(typingTimeout);
  typingTimeout = setTimeout(() => {
    typing = false;
    socket.emit('stop_typing', { room });
  }, 3000);
});

socket.on('user_typing', (data) => {
  if (data.username !== currentUser) { // Prevent showing typing indicator for self
    typingIndicator.textContent = `${data.username} is typing...`;
    typingIndicator.style.display = 'block';
  }
});

socket.on('user_typing_stopped', (data) => {
  typingIndicator.style.display = 'none';
});

function appendMessage(data, isCurrentUser) {
  const messageElement = document.createElement('div');
  messageElement.classList.add('message');
  if (isCurrentUser) {
    messageElement.classList.add('current-user');
  }

  // Avatar Link
  const avatarLink = document.createElement('a');
  avatarLink.href = `/profile/${encodeURIComponent(data.user)}`;
  avatarLink.setAttribute('data-bs-toggle', 'tooltip');
  avatarLink.setAttribute('data-bs-placement', 'top');
  avatarLink.setAttribute('title', data.user);

  const avatar = document.createElement('img');
  avatar.src = data.profile_picture || '/static/images/default_avatar.png';
  avatar.alt = `${data.user}'s avatar`;
  avatar.classList.add('avatar');

  avatarLink.appendChild(avatar);

  // Message Content
  const messageContent = document.createElement('div');
  messageContent.classList.add('message-content');

  const messageHeader = document.createElement('div');
  messageHeader.classList.add('message-header');

  const usernameLink = document.createElement('a');
  usernameLink.href = `/profile/${encodeURIComponent(data.user)}`;
  usernameLink.classList.add('username');
  usernameLink.setAttribute('data-bs-toggle', 'tooltip');
  usernameLink.setAttribute('data-bs-placement', 'top');
  usernameLink.setAttribute('title', data.user);
  usernameLink.textContent = data.user || 'Unknown';

  const timestampSpan = document.createElement('span');
  timestampSpan.classList.add('timestamp');
  timestampSpan.textContent = data.timestamp || '';

  // Actual message text
  const messageText = document.createElement('div');
  messageText.classList.add('message-text');
  messageText.textContent = data.message || '';

  // Add an image if image_url is present
  if (data.image_url) {
    const msgImage = document.createElement('img');
    msgImage.src = data.image_url;
    msgImage.alt = 'Attached image';
    msgImage.classList.add('message-image');
    msgImage.style.maxWidth = '200px';
    msgImage.style.display = 'block';
    msgImage.style.marginTop = '0.5rem';
    messageText.appendChild(msgImage);
  }

  messageHeader.appendChild(usernameLink);
  messageHeader.appendChild(timestampSpan);
  messageContent.appendChild(messageHeader);
  messageContent.appendChild(messageText);

  // Assemble Message
  if (!isCurrentUser) {
    messageElement.appendChild(avatarLink);
  }
  messageElement.appendChild(messageContent);
  if (isCurrentUser) {
    // Clone avatarLink to avoid duplicate IDs/tooltips
    const clonedAvatarLink = avatarLink.cloneNode(true);
    messageElement.appendChild(clonedAvatarLink);
  }

  messagesContainer.appendChild(messageElement);
  scrollToBottom();

  // Reinitialize tooltips for new elements
  const tooltipTriggerList = [].slice.call(
    messageElement.querySelectorAll('[data-bs-toggle="tooltip"]')
  );
  tooltipTriggerList.forEach(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });
}

// Online Users Handling
socket.on('update_users', (onlineUsers) => {
  // Hide loading indicator
  onlineUsersLoading.style.display = 'none';

  // For each list item, update online status based on onlineUsers list
  onlineUsersList.querySelectorAll('li').forEach(li => {
    const username = li.getAttribute('data-username');
    const statusIndicator = li.querySelector('.status-indicator');
    if(onlineUsers.some(user => user.username === username)) {
      statusIndicator.style.display = 'inline-block'; // Show green dot for online
    } else {
      statusIndicator.style.display = 'none'; // Hide for offline
    }
  });
});

// Attach click listeners to user list items for DM initiation
document.querySelectorAll('#online-users li').forEach(li => {
  li.addEventListener('click', () => {
    const username = li.getAttribute('data-username');
    if(username && username !== currentUser) { // Prevent DM to self
      window.location.href = `/dm/${encodeURIComponent(username)}`;
    }
  });
});

// Notifications
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

socket.on('notification', (data) => {
  const action = data.message.includes('joined') ? 'joined' : 'left';
  showNotification(`${data.user} has ${action} the room.`, action === 'joined' ? 'success' : 'warning');
});

// Room Switching
const roomSelect = document.getElementById('room-select');
if(roomSelect) { // Check if roomSelect exists on page
  roomSelect.addEventListener('change', () => {
    const newRoom = roomSelect.value;
    // Show loading indicators
    messagesLoading.style.display = 'flex';
    onlineUsersLoading.style.display = 'flex';
    window.location.href = `/${encodeURIComponent(newRoom)}`;
  });
}
