// Connect to the Socket.IO server
const socket = io();

// Get the current user's username and room name from hidden elements
const currentUsername = document.getElementById('current-username').value;
let currentRoom = document.getElementById('room').value; // Use `let` to allow room switching

// Join the specified chat room when the page loads
socket.emit('join', { room: currentRoom });

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
    const currentRoom = document.getElementById('room').value; // Get the current room name
    socket.emit('message', { message, room: currentRoom });
    document.getElementById('message').value = ''; // Clear input field
  }
});


// Listen for notifications when the user joins a room
socket.on('notification', (data) => {
  const messagesContainer = document.getElementById('messages');
  const notificationElement = document.createElement('div');

  notificationElement.classList.add('notification');
  notificationElement.textContent = `${data.user} has joined the room.`;

  messagesContainer.appendChild(notificationElement);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
});

// Listen for notifications when the user leaves a room
socket.on('leave-notification', (data) => {
  const messagesContainer = document.getElementById('messages');
  const notificationElement = document.createElement('div');

  notificationElement.classList.add('notification');
  notificationElement.textContent = `${data.user} has left the room.`;

  messagesContainer.appendChild(notificationElement);
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
});

// Handle room selection changes for switching rooms dynamically
document.getElementById('room-select').addEventListener('change', (event) => {
  const newRoom = event.target.value;

  if (newRoom !== currentRoom) {
    // Leave the current room
    socket.emit('leave', { room: currentRoom });

    // Update current room and join the new one
    currentRoom = newRoom;
    socket.emit('join', { room: currentRoom });

    // Clear message history and update room display
    document.getElementById('messages').innerHTML = '';
    document.getElementById('room').value = currentRoom;
  }
});

// Emit a direct message event
socket.emit('direct_message', { receiverId, message });

// Listen for incoming DMs
socket.on('direct_message', (data) => {
  if (data.senderId === currentUserId || data.receiverId === currentUserId) {
    // Update the DM UI in real-time
    loadDmMessages(data.senderId === currentUserId ? data.receiverId : data.senderId);
  }
});

document.getElementById('send-dm').addEventListener('click', () => {
  const message = document.getElementById('dm-message').value.trim();
  const receiverId = document.getElementById('receiver-id').value; // Hidden input with receiver ID

  if (message) {
    fetch('/send_dm', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ receiver_id: receiverId, message })
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        // Reload message history or append the new message
        loadDmMessages(receiverId);
        document.getElementById('dm-message').value = ''; // Clear input
      }
    });
  }
});

function loadDmMessages(receiverId) {
  fetch(`/dm/${receiverId}`)
    .then(response => response.json())
    .then(messages => {
      const dmMessages = document.getElementById('dm-messages');
      dmMessages.innerHTML = ''; // Clear current messages
      messages.forEach(msg => {
        const messageElement = document.createElement('div');
        messageElement.className = 'message';
        messageElement.innerHTML = `
          <strong>${msg.sender_id === currentUserId ? 'You' : 'Them'}:</strong>
          ${msg.message} <span class="timestamp">${msg.formatted_timestamp}</span>
        `;
        dmMessages.appendChild(messageElement);
      });
    });
}
