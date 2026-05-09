// DOM Elements
const setupModal = document.getElementById('setup-modal');
const appContainer = document.getElementById('app-container');
const connectBtn = document.getElementById('connect-btn');
const registerBtn = document.getElementById('register-btn');
const setupError = document.getElementById('setup-error');
const setupSuccess = document.getElementById('setup-success');
const currentUsernameEl = document.getElementById('current-username');
const peerListEl = document.getElementById('peer-list');
const chatTitle = document.getElementById('chat-title');
const chatSubtitle = document.getElementById('chat-subtitle');
const messageHistory = document.getElementById('message-history');
const chatForm = document.getElementById('chat-form');
const messageInput = document.getElementById('message-input');

// Application State
let currentUser = '';
let activeTarget = 'broadcast'; // 'broadcast' or username
let allMessages = []; // Cache of all messages
let knownPeers = [];
let unreadChannels = new Set(); // Tracks which channels have new messages

// Notification Sound
const notificationSound = new Audio('/notification-sound-for-messenger-messages.mp3');

// ==========================================
// Setup & Authentication
// ==========================================

registerBtn.addEventListener('click', async () => {
    const trackerIp = document.getElementById('tracker-ip').value;
    const trackerPort = document.getElementById('tracker-port').value;
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    if (!username || !password) {
        showError('Username and password required');
        return;
    }

    registerBtn.disabled = true;
    registerBtn.textContent = 'Registering...';
    hideMessages();

    try {
        const res = await fetch('/api/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                username, password, tracker_ip: trackerIp, tracker_port: parseInt(trackerPort)
            })
        });

        const data = await res.json();

        if (res.ok) {
            showSuccess(data.message || 'Registration successful! You can now Join.');
        } else {
            showError(data.error || 'Registration failed');
        }
    } catch (err) {
        showError('Network error connecting to local node');
    } finally {
        registerBtn.disabled = false;
        registerBtn.textContent = 'Sign Up';
    }
});

connectBtn.addEventListener('click', async () => {
    const trackerIp = document.getElementById('tracker-ip').value;
    const trackerPort = document.getElementById('tracker-port').value;
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    if (!username || !password) {
        showError('Username and password required');
        return;
    }

    connectBtn.disabled = true;
    connectBtn.textContent = 'Connecting...';

    try {
        const res = await fetch('/api/setup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                username, password, tracker_ip: trackerIp, tracker_port: parseInt(trackerPort)
            })
        });

        const data = await res.json();

        if (res.ok) {
            // Success!
            currentUser = username;
            currentUsernameEl.textContent = username;
            setupModal.classList.add('hidden');
            appContainer.classList.remove('hidden');
            
            // Start polling
            pollPeers();
            pollMessages();
            setInterval(pollPeers, 5000);
            setInterval(pollMessages, 2000);
        } else {
            showError(data.error || 'Failed to connect');
        }
    } catch (err) {
        showError('Network error connecting to local node');
    } finally {
        connectBtn.disabled = false;
        connectBtn.textContent = 'Join Network';
    }
});

function showSuccess(msg) {
    setupSuccess.textContent = msg;
    setupSuccess.classList.remove('hidden');
    setupError.classList.add('hidden');
}

function showError(msg) {
    setupError.textContent = msg;
    setupError.classList.remove('hidden');
    setupSuccess.classList.add('hidden');
}

function hideMessages() {
    setupError.classList.add('hidden');
    setupSuccess.classList.add('hidden');
}

// ==========================================
// Peer Management (Sidebar)
// ==========================================

async function pollPeers() {
    try {
        const res = await fetch('/api/peers');
        if (!res.ok) return;
        const data = await res.json();
        
        // Don't show ourselves in the list
        knownPeers = data.peers.filter(p => p.username !== currentUser);
        renderPeerList();
    } catch (e) {
        console.error("Failed to fetch peers");
    }
}

function renderPeerList() {
    peerListEl.innerHTML = '';
    
    // Make sure broadcast is active if selected
    const broadcastEl = document.querySelector('[data-target="broadcast"]');
    if (activeTarget === 'broadcast') {
        broadcastEl.classList.add('active');
    } else {
        broadcastEl.classList.remove('active');
    }

    // Show "New" on broadcast if unread
    const broadcastBadge = unreadChannels.has('broadcast') ? '<span class="unread-badge">New</span>' : '';
    broadcastEl.querySelector('.peer-info').innerHTML = `
        <span class="peer-name">Broadcast (All) ${broadcastBadge}</span>
        <span class="peer-status">Public Channel</span>
    `;

    // Add click listener to broadcast
    broadcastEl.onclick = () => selectChannel('broadcast');

    knownPeers.forEach(peer => {
        const el = document.createElement('div');
        el.className = `peer-item ${activeTarget === peer.username ? 'active' : ''}`;
        el.dataset.target = peer.username;
        
        // Generate an initial for the avatar
        const initial = peer.username.charAt(0).toUpperCase();
        const unreadBadge = unreadChannels.has(peer.username) ? '<span class="unread-badge">New</span>' : '';
        
        el.innerHTML = `
            <div class="peer-avatar">${initial}</div>
            <div class="peer-info">
                <span class="peer-name">${peer.username} ${unreadBadge}</span>
                <span class="peer-status">Online • ${peer.ip}:${peer.port}</span>
            </div>
        `;
        
        el.onclick = () => selectChannel(peer.username);
        peerListEl.appendChild(el);
    });
}

function selectChannel(target) {
    activeTarget = target;
    unreadChannels.delete(target); // Clear unread status
    renderPeerList(); // update active class
    
    if (target === 'broadcast') {
        chatTitle.textContent = 'Broadcast (All)';
        chatSubtitle.textContent = 'Public Channel';
    } else {
        chatTitle.textContent = target;
        chatSubtitle.textContent = 'Direct Message';
    }
    
    renderMessages(); // filter messages for this channel
}

// ==========================================
// Chat & Messaging
// ==========================================

async function pollMessages() {
    try {
        const res = await fetch('/api/messages');
        if (!res.ok) return;
        const data = await res.json();
        
        // Only re-render if we have new messages
        if (data.messages.length > allMessages.length) {
            const newMessages = data.messages.slice(allMessages.length);
            
            newMessages.forEach(msg => {
                // If the message is NOT from us
                if (msg.from !== currentUser) {
                    const channel = msg.channel === 'broadcast' ? 'broadcast' : msg.from;
                    
                    // Mark as unread if it's not the active chat
                    if (channel !== activeTarget) {
                        unreadChannels.add(channel);
                        renderPeerList();
                    }
                    
                    // Play notification sound
                    notificationSound.play().catch(e => console.log("Sound play failed:", e));
                }
            });

            allMessages = data.messages;
            renderMessages();
        }
    } catch (e) {
        console.error("Failed to fetch messages");
    }
}

function renderMessages() {
    messageHistory.innerHTML = '';
    
    // Filter messages for current view
    const filteredMessages = allMessages.filter(msg => {
        if (activeTarget === 'broadcast') {
            return msg.channel === 'broadcast';
        } else {
            // Direct messages involving the active target
            return msg.channel === 'direct' && 
                   (msg.to === activeTarget || msg.from === activeTarget);
        }
    });

    filteredMessages.forEach(msg => {
        const isSentByMe = msg.from === currentUser;
        
        const el = document.createElement('div');
        el.className = `message ${isSentByMe ? 'sent' : 'received'}`;
        
        // Only show sender name if it's received
        const senderHtml = !isSentByMe ? `<div class="msg-sender">${msg.from}</div>` : '';
        
        el.innerHTML = `
            ${senderHtml}
            <div class="msg-bubble">${escapeHtml(msg.text)}</div>
            <div class="msg-meta">${msg.timestamp}</div>
        `;
        
        messageHistory.appendChild(el);
    });

    // Auto scroll to bottom
    messageHistory.scrollTop = messageHistory.scrollHeight;
}

chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const text = messageInput.value.trim();
    if (!text) return;
    
    // Clear input immediately for good UX
    messageInput.value = '';
    
    // Optimistically add to UI (the backend poll will eventually catch up too)
    const optimisticMsg = {
        from: currentUser,
        to: activeTarget,
        text: text,
        timestamp: new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit', second:'2-digit'}),
        channel: activeTarget === 'broadcast' ? 'broadcast' : 'direct'
    };
    
    allMessages.push(optimisticMsg);
    renderMessages();
    
    try {
        await fetch('/api/send_message', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ target: activeTarget, message: text })
        });
        // We could handle failure here and remove the optimistic message, but ignoring for simplicity
    } catch (err) {
        console.error("Failed to send message");
    }
});

function escapeHtml(unsafe) {
    return unsafe
         .replace(/&/g, "&amp;")
         .replace(/</g, "&lt;")
         .replace(/>/g, "&gt;")
         .replace(/"/g, "&quot;")
         .replace(/'/g, "&#039;");
}
