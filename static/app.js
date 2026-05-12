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
        return;
    }

    registerBtn.disabled = true;
    registerBtn.textContent = 'Đang đăng ký…';

    try {
        const res = await fetch('/api/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
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

    try {
        const res = await fetch('/api/setup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
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

async function pollPeers() {
    try {
        const res = await fetch('/api/peers');
        if (!res.ok) return;
        const data = await res.json();
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
    });
}

function selectChannel(target) {
    activeTarget = target;
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
async function pollMessages() {
    try {
        const res = await fetch('/api/messages');
        if (!res.ok) return;
        const data = await res.json();
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
    }
}

function renderMessages() {
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

    try {
        await fetch('/api/send_message', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ target: activeTarget, message: text })
        });
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
}
