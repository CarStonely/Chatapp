// Connect to the Socket.IO server
const socket = io();

// Grab references to key DOM elements
const currentUsername = document.getElementById('current-username').value;
let currentRoom = document.getElementById('room').value; 
const messageInput = document.getElementById('message');
const sendButton = document.getElementById('send');
const messagesContainer = document.getElementById('messages');
const roomSelect = document.getElementById('room-select');
const roomHiddenInput = document.getElementById('room');

// Typing indicator
const typingIndicator = document.getElementById('typing-indicator'); 
// e.g. <div id="typing-indicator" style="display:none;"></div> in your HTML

let typing = false;
let typingTimeout;

// Join the specified chat room on page load
socket.emit('join', { room: currentRoom });

// Send a message
function sendMessage() {
  const message = messageInput.value.trim();
  if (message) {
    // Immediately stop typing
    stopTyping();
    socket.emit('message', { message, room: currentRoom });
    messageInput.value = ''; // Clear the input field
  }
}

// Listen for click on the "Send" button
sendButton.addEventListener('click', () => {
  sendMessage();
});

// (Optional) Listen for "Enter" key to send message
messageInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') {
    e.preventDefault();
    sendMessage();
  }
});

// ===== TYPING INDICATOR LOGIC =====
function startTyping() {
  if (!typing) {
    typing = true;
    socket.emit('typing', { room: currentRoom });
  }
  clearTimeout(typingTimeout);
  typingTimeout = setTimeout(stopTyping, 3000);
}

function stopTyping() {
  if (typing) {
    typing = false;
    socket.emit('stop_typing', { room: currentRoom });
  }
}
// Trigger startTyping on each key press
messageInput.addEventListener('input', () => {
  if (messageInput.value.length > 0) {
    startTyping();
  } else {
    // If user deletes everything, we can immediately stop
    stopTyping();
  }
});

// Handle room selection changes (dynamic Socket.IO approach)
roomSelect.addEventListener('change', (event) => {
  const newRoom = event.target.value;
  if (newRoom !== currentRoom) {
    socket.emit('leave', { room: currentRoom });
    currentRoom = newRoom;
    socket.emit('join', { room: currentRoom });
    messagesContainer.innerHTML = '';
    roomHiddenInput.value = currentRoom;
  }
});

// Listen for user joining notifications
socket.on('notification', (data) => {
  const notificationElement = document.createElement('div');
  notificationElement.classList.add('notification');
  notificationElement.textContent = `${data.user} has joined the room.`;
  messagesContainer.appendChild(notificationElement);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
});

// Listen for user leaving notifications
socket.on('leave-notification', (data) => {
  const notificationElement = document.createElement('div');
  notificationElement.classList.add('notification');
  notificationElement.textContent = `${data.user} has left the room.`;
  messagesContainer.appendChild(notificationElement);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
});

// Listen for incoming messages
socket.on('message', (data) => {
  const messageElement = document.createElement('div');
  messageElement.classList.add('message');
  
  if (data.user === currentUsername) {
    messageElement.classList.add('current-user');
  }

  // Create avatar element
  const avatar = document.createElement('img');
  avatar.src = data.profile_picture || '/static/images/default_avatar.png';
  avatar.alt = `${data.user}'s avatar`;
  avatar.classList.add('avatar');

  // Create message content
  const content = document.createElement('div');
  content.innerHTML = `
    <span class="username">${data.user}</span>:
    <span>${data.message}</span>
    <span class="timestamp">${new Date(data.timestamp).toLocaleTimeString()}</span>
  `;

  messageElement.appendChild(avatar);
  messageElement.appendChild(content);

  // Append to container and auto-scroll
  messagesContainer.appendChild(messageElement);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
});

// ===== RECEIVING TYPING UPDATES =====
socket.on('user_typing', (data) => {
  const { username, action } = data;
  if (action === 'typing') {
    // Show "username is typing..." 
    typingIndicator.innerText = `${username} is typing...`;
    typingIndicator.style.display = 'block';
  } else if (action === 'stopped') {
    typingIndicator.innerText = '';
    typingIndicator.style.display = 'none';
  }
});

// Example: handle a click on a username
document.addEventListener('click', (event) => {
  if (event.target.classList.contains('username')) {
    console.log(`Username link clicked: ${event.target.textContent}`);
  }
});
