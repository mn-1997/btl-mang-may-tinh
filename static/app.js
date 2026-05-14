// <<<<<<< HEAD
// // DOM Elements
// const setupModal = document.getElementById('setup-modal');
// const appContainer = document.getElementById('app-container');
// const connectBtn = document.getElementById('connect-btn');
// const registerBtn = document.getElementById('register-btn');
// const setupError = document.getElementById('setup-error');
// const setupSuccess = document.getElementById('setup-success');
// const currentUsernameEl = document.getElementById('current-username');
// const peerListEl = document.getElementById('peer-list');
// const chatTitle = document.getElementById('chat-title');
// const chatSubtitle = document.getElementById('chat-subtitle');
// const messageHistory = document.getElementById('message-history');
// const chatForm = document.getElementById('chat-form');
// const messageInput = document.getElementById('message-input');

// // Application State
// let currentUser = '';
// let activeTarget = 'broadcast'; // 'broadcast' or username
// let allMessages = []; // Cache of all messages
// let knownPeers = [];
// let unreadChannels = new Set(); // Tracks which channels have new messages

// // Notification Sound
// const notificationSound = new Audio('/notification-sound-for-messenger-messages.mp3');

// // ==========================================
// // Setup & Authentication
// // ==========================================

// registerBtn.addEventListener('click', async () => {
//     const trackerIp = document.getElementById('tracker-ip').value;
//     const trackerPort = document.getElementById('tracker-port').value;
//     const username = document.getElementById('username').value;
//     const password = document.getElementById('password').value;

//     if (!username || !password) {
//         showError('Username and password required');
=======
// ===================================================
// DOM References
// ===================================================
const authSection      = document.getElementById('auth-section');
const chatSection      = document.getElementById('chat-section');
const loginBtn         = document.getElementById('login-btn');
const registerBtn      = document.getElementById('register-btn');
const authMsg          = document.getElementById('auth-msg');
const loggedUser       = document.getElementById('logged-user');
const channelList      = document.getElementById('channel-list');
const chatTargetName   = document.getElementById('chat-target-name');
const messageWindow    = document.getElementById('message-window');
const messageInput     = document.getElementById('message-input');
const sendBtn          = document.getElementById('send-btn');
const refreshBtn       = document.getElementById('refresh-btn');
const logoutBtn        = document.getElementById('logout-btn');
const newMsgBanner     = document.getElementById('new-msg-banner');
const bannerCloseBtn   = document.getElementById('banner-close-btn');

// ===================================================
// Application State
// ===================================================
let currentUser       = '';
let activeTarget      = 'broadcast';   // 'broadcast' or a peer username
let allMessages       = [];            // full message cache
let knownPeers        = [];            // list of online peers
let unreadChannels    = new Set();     // channels with unread messages
let pollPeersId       = null;
let pollMsgId         = null;
let bannerTimeout     = null;

// ===================================================
// AUTH — Register
// ===================================================
registerBtn.addEventListener('click', async () => {
    const { trackerIp, trackerPort, username, password } = getFormValues();

    if (!username || !password) {
        setAuthMsg('Vui lòng nhập tên đăng nhập và mật khẩu.', false);
>>>>>>> origin/frontend
return;
    }

registerBtn.disabled = true;
<<<<<<< HEAD
registerBtn.textContent = 'Registering...';
hideMessages();
=======
    registerBtn.textContent = 'Đang đăng ký…';
>>>>>>> origin/frontend

try {
    const res = await fetch('/api/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
<<<<<<< HEAD
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
=======
                username,
                password,
                tracker_ip: trackerIp,
                tracker_port: parseInt(trackerPort)
            })
        });
        const data = await res.json();
        if (res.ok) {
            setAuthMsg('Đăng ký thành công! Hãy đăng nhập.', true);
        } else {
            setAuthMsg('Lỗi: ' + (data.error || 'Đăng ký thất bại'), false);
        }
    } catch (_) {
        setAuthMsg('Lỗi kết nối mạng.', false);
    } finally {
        registerBtn.disabled = false;
        registerBtn.textContent = 'Đăng ký';
    }
});

// ===================================================
// AUTH — Login  →  calls /api/setup (login + submit-info)
// ===================================================
loginBtn.addEventListener('click', async () => {
    const { trackerIp, trackerPort, username, password } = getFormValues();

    if (!username || !password) {
        setAuthMsg('Vui lòng nhập tên đăng nhập và mật khẩu.', false);
        return;
    }

    loginBtn.disabled = true;
    loginBtn.textContent = 'Đang kết nối…';
>>>>>>> origin/frontend

    try {
        const res = await fetch('/api/setup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
<<<<<<< HEAD
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
=======
                username,
                password,
                tracker_ip: trackerIp,
                tracker_port: parseInt(trackerPort)
            })
        });
        const data = await res.json();

        if (res.ok) {
            currentUser = username;
            loggedUser.textContent = username;

            // Switch views
            authSection.style.display  = 'none';
            chatSection.style.display  = 'flex';

            // Initial fetch
            await pollPeers();
            await pollMessages();

            // Start periodic polling
            pollPeersId = setInterval(pollPeers,    5000);
            pollMsgId   = setInterval(pollMessages, 2000);
        } else {
            setAuthMsg('Lỗi: ' + (data.error || 'Đăng nhập thất bại'), false);
        }
    } catch (_) {
        setAuthMsg('Lỗi kết nối mạng.', false);
    } finally {
        loginBtn.disabled = false;
        loginBtn.textContent = 'Đăng nhập';
    }
});

function getFormValues() {
    return {
        trackerIp:   document.getElementById('tracker-ip').value.trim(),
        trackerPort: document.getElementById('tracker-port').value.trim(),
        username:    document.getElementById('username').value.trim(),
        password:    document.getElementById('password').value.trim()
    };
}

function setAuthMsg(msg, isOk) {
    authMsg.textContent  = msg;
    authMsg.style.color  = isOk ? 'green' : 'red';
}

// ===================================================
// LOGOUT
// ===================================================
logoutBtn.addEventListener('click', () => {
    clearInterval(pollPeersId);
    clearInterval(pollMsgId);

    // Reset state
    currentUser    = '';
    activeTarget   = 'broadcast';
    allMessages    = [];
    knownPeers     = [];
    unreadChannels.clear();

    // Reset UI
    messageWindow.innerHTML  = '';
    channelList.innerHTML    = '';
    chatTargetName.textContent = 'Broadcast (Tất cả)';
    hideBanner();

    chatSection.style.display = 'none';
    authSection.style.display = 'block';
    setAuthMsg('', true);
});

// ===================================================
// CHANNEL / PEER LIST  →  /api/peers
// ===================================================
refreshBtn.addEventListener('click', pollPeers);
>>>>>>> origin/frontend

async function pollPeers() {
    try {
        const res = await fetch('/api/peers');
        if (!res.ok) return;
        const data = await res.json();
<<<<<<< HEAD

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
=======
        // Exclude ourselves from the list
        knownPeers = (data.peers || []).filter(p => p.username !== currentUser);
        renderChannelList();
    } catch (_) {
        console.error('Lỗi lấy danh sách peer');
    }
}

function renderChannelList() {
    channelList.innerHTML = '';

    // --- Broadcast channel ---
    const broadcastEl = document.createElement('div');
    broadcastEl.className = 'channel-item' + (activeTarget === 'broadcast' ? ' active' : '');
    broadcastEl.dataset.target = 'broadcast';

    const bBadge = unreadChannels.has('broadcast')
        ? '<span class="unread-badge">Mới</span>' : '';
    broadcastEl.innerHTML = '🌐 Broadcast (Tất cả) ' + bBadge;
    broadcastEl.onclick = () => selectChannel('broadcast');
    channelList.appendChild(broadcastEl);

    // --- Direct message peers ---
    knownPeers.forEach(peer => {
        const el = document.createElement('div');
        el.className = 'channel-item' + (activeTarget === peer.username ? ' active' : '');
        el.dataset.target = peer.username;

        const pBadge = unreadChannels.has(peer.username)
            ? '<span class="unread-badge">Mới</span>' : '';
        el.innerHTML =
            '👤 ' + escapeHtml(peer.username) + ' ' + pBadge +
            '<br><small>' + escapeHtml(peer.ip) + ':' + peer.port + '</small>';
        el.onclick = () => selectChannel(peer.username);
        channelList.appendChild(el);
>>>>>>> origin/frontend
    });
}

function selectChannel(target) {
    activeTarget = target;
<<<<<<< HEAD
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

=======
    unreadChannels.delete(target);
    chatTargetName.textContent =
        target === 'broadcast' ? 'Broadcast (Tất cả)' : target;
    renderChannelList();
    renderMessages();
    hideBanner();
}

// ===================================================
// MESSAGES — polling  →  /api/messages
// ===================================================
>>>>>>> origin/frontend
async function pollMessages() {
    try {
        const res = await fetch('/api/messages');
        if (!res.ok) return;
        const data = await res.json();
<<<<<<< HEAD

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
=======
        const msgs = data.messages || [];

        if (msgs.length > allMessages.length) {
            const newMsgs = msgs.slice(allMessages.length);
            let hasNewInOtherChannel = false;

            newMsgs.forEach(msg => {
                if (msg.from !== currentUser) {
                    const channel = msg.channel === 'broadcast'
                        ? 'broadcast' : msg.from;

                    if (channel !== activeTarget) {
                        unreadChannels.add(channel);
                        hasNewInOtherChannel = true;
                    }
                    // Always show banner for incoming messages
                    showBanner();
                }
            });

            allMessages = msgs;
            renderChannelList();
            renderMessages();
        }
    } catch (_) {
        console.error('Lỗi lấy tin nhắn');
>>>>>>> origin/frontend
    }
}

function renderMessages() {
<<<<<<< HEAD
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
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
        channel: activeTarget === 'broadcast' ? 'broadcast' : 'direct'
    };

    allMessages.push(optimisticMsg);
    renderMessages();

=======
    messageWindow.innerHTML = '';

    const filtered = allMessages.filter(msg => {
        if (activeTarget === 'broadcast') {
            return msg.channel === 'broadcast';
        }
        // Direct messages involving the active peer
        return msg.channel === 'direct' &&
               (msg.to === activeTarget || msg.from === activeTarget);
    });

    filtered.forEach(msg => {
        const isMine = (msg.from === currentUser);
        const div    = document.createElement('div');
        div.className = 'msg-row ' + (isMine ? 'msg-sent' : 'msg-received');

        const senderHtml = !isMine
            ? '<div class="msg-sender">' + escapeHtml(msg.from) + '</div>' : '';

        div.innerHTML =
            senderHtml +
            '<div class="msg-bubble">' + escapeHtml(msg.text) + '</div>' +
            '<div class="msg-meta">' + escapeHtml(msg.timestamp || '') + '</div>';

        messageWindow.appendChild(div);
    });

    // Auto-scroll to latest message
    messageWindow.scrollTop = messageWindow.scrollHeight;
}

// ===================================================
// SEND MESSAGE  →  /api/send_message
// ===================================================
sendBtn.addEventListener('click', sendMessage);

messageInput.addEventListener('keydown', e => {
    if (e.key === 'Enter') sendMessage();
});

async function sendMessage() {
    const text = messageInput.value.trim();
    if (!text) return;
    messageInput.value = '';

    // Optimistic local append (no edit/delete — immutable)
    const optimistic = {
        from:      currentUser,
        to:        activeTarget,
        text:      text,
        timestamp: new Date().toLocaleTimeString([], {
            hour: '2-digit', minute: '2-digit', second: '2-digit'
        }),
        channel:   activeTarget === 'broadcast' ? 'broadcast' : 'direct'
    };
    allMessages.push(optimistic);
    renderMessages();

>>>>>>> origin/frontend
    try {
        await fetch('/api/send_message', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ target: activeTarget, message: text })
        });
<<<<<<< HEAD
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
=======
    } catch (_) {
        console.error('Lỗi gửi tin nhắn');
    }
}

// ===================================================
// NOTIFICATION BANNER
// ===================================================
function showBanner() {
    newMsgBanner.style.display = 'flex';
    clearTimeout(bannerTimeout);
    bannerTimeout = setTimeout(hideBanner, 5000);
}

function hideBanner() {
    newMsgBanner.style.display = 'none';
}

bannerCloseBtn.addEventListener('click', hideBanner);

// ===================================================
// UTILITY
// ===================================================
function escapeHtml(str) {
    return String(str)
        .replace(/&/g,  '&amp;')
        .replace(/</g,  '&lt;')
        .replace(/>/g,  '&gt;')
        .replace(/"/g,  '&quot;')
        .replace(/'/g,  '&#039;');
>>>>>>> origin/frontend
}
