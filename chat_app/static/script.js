// Connect to the Socket.IO server
const socket = io();

// Get the current user's username from a hidden element or script tag
const currentUsername = document.getElementById('current-username').value;

// Listen for messages from the server
socket.on('message', (data) => {
  const messagesContainer = document.getElementById('messages');
  const messageElement = document.createElement('div');

  // Add message classes based on the user
  messageElement.classList.add('message');
  if (data.user === currentUsername) {
    messageElement.classList.add('current-user');
  }

  // Format and add the message with timestamp
  const timestamp = new Date(data.timestamp).toLocaleString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: true,
  });

  messageElement.innerHTML = `
    <span class="username">${data.user}:</span>
    <span>${data.message}</span>
    <span class="timestamp">${timestamp}</span>
  `;

  // Append the message and scroll to the bottom
  messagesContainer.appendChild(messageElement);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
});

// Emit a message when the user sends one
document.getElementById('send').addEventListener('click', () => {
  const message = document.getElementById('message').value.trim();

  if (message) {
    // Emit message event with content
    socket.emit('message', { message });
    document.getElementById('message').value = ''; // Clear input field
  }
});
