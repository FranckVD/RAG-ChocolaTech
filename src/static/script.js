// Ya no usamos localStorage para nada sensible.
let logoutTimer;

function showNotification(message, type = 'info') {
    const container = document.getElementById('notification-container');
    const notification = document.createElement('div');
    notification.className = `notification ${type} show`;
    
    const icon = type === 'error' ? 'fa-exclamation-triangle' : 'fa-info-circle';
    
    notification.innerHTML = `
        <div class="flex items-center gap-3">
            <div class="notification-icon">
                <i class="fas ${icon}"></i>
            </div>
            <div class="flex flex-col">
                <span class="text-xs font-bold uppercase tracking-wider opacity-50">${type === 'error' ? 'Seguridad' : 'Sistema'}</span>
                <span class="text-sm font-medium">${message}</span>
            </div>
        </div>
    `;
    container.appendChild(notification);
    
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}

function startLogoutTimer(expiresAt) {
    if (logoutTimer) clearTimeout(logoutTimer);
    
    const now = Math.floor(Date.now() / 1000);
    const remainingSeconds = expiresAt - now;
    
    if (remainingSeconds <= 0) {
        logout();
        return;
    }
    
    logoutTimer = setTimeout(() => {
        showNotification("Tu sesión ha expirado. Redirigiendo...", "error");
        setTimeout(() => logout(), 3000);
    }, remainingSeconds * 1000);
}

async function checkSession() {
    try {
        console.log("Verificando sesión...");
        const response = await fetch('/api/me');
        if (response.ok) {
            const user = await response.json();
            console.log("Datos de usuario recibidos:", user);
            document.getElementById('display-name').innerText = user.nombre;
            document.getElementById('login-modal').classList.add('hidden');
            
            if (user.expires_at) {
                console.log("Iniciando temporizador de cierre de sesión para:", new Date(user.expires_at * 1000).toLocaleString());
                startLogoutTimer(user.expires_at);
            }
            return true;
        } else {
            console.warn("La respuesta de sesión no fue OK:", response.status);
        }
    } catch (e) {
        console.error("Error verificando sesión:", e);
    }
    document.getElementById('login-modal').classList.remove('hidden');
    return false;
}

// Inicialización
document.addEventListener("DOMContentLoaded", () => {
    const userInput = document.getElementById('user-input');
    
    // Verificamos sesión con el servidor directamente
    checkSession();

    userInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });
});

async function login() {
    const user = document.getElementById('login-user').value.trim();
    const pass = document.getElementById('login-password').value.trim();
    
    if (!user || !pass) {
        showNotification("Por favor completa todos los campos.", "error");
        return;
    }
    
    const formData = new FormData();
    formData.append('username', user);
    formData.append('password', pass);
    
    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            const data = await response.json();
            // No guardamos nada en localStorage. Recargamos para que checkSession() haga su magia.
            location.reload();
        } else {
            const err = await response.json();
            showNotification(err.detail || "Error al iniciar sesión.", "error");
        }
    } catch (error) {
        showNotification("Error de conexión con el servidor.", "error");
    }
}

async function logout() {
    try {
        await fetch('/api/logout', { method: 'POST' });
    } catch (e) {}
    location.reload();
}

async function enviarPregunta() {
    const input = document.getElementById('user-input');
    const text = input.value.trim();
    if (!text) return;

    input.value = '';
    input.style.height = 'auto';

    appendMessage('user', text);
    
    const loadingId = 'loading-' + Date.now();
    appendLoading(loadingId);
    scrollToBottom();

    try {
        const response = await fetch('/api/consultar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ pregunta: text })
        });
        
        if (response.status === 401) {
            showNotification("Sesión expirada. Redirigiendo...", "error");
            setTimeout(() => logout(), 1500);
            return;
        }

        const data = await response.json();
        removeLoading(loadingId);
        appendMessage('bot', data.respuesta);
        
    } catch (error) {
        removeLoading(loadingId);
        appendMessage('bot', "❌ Error de conexión.");
    }
    scrollToBottom();
}

// Configurar Marked
marked.setOptions({ headerIds: false, mangle: false, breaks: true });

function appendMessage(role, text) {
    const isBot = role === 'bot';
    const chatContainer = document.getElementById('chat-container');
    const contentHtml = isBot ? marked.parse(text) : text;
    
    const html = `<div class="flex gap-3 ${isBot ? '' : 'flex-row-reverse'} mb-6 message-animate">` +
        `<div class="w-8 h-8 rounded-lg ${isBot ? 'bg-indigo-500' : 'bg-slate-700'} flex-shrink-0 flex items-center justify-center text-white text-[10px] mt-1 shadow-md">` +
            `<i class="fas fa-${isBot ? 'robot' : 'user'}"></i>` +
        `</div>` +
        `<div class="chat-bubble ${isBot ? 'items-start' : 'items-end'} flex-1">` +
            `<div class="chat-bubble-content ${isBot ? 'bg-[#1e293b] text-slate-300 rounded-tl-none border-slate-700' : 'bg-indigo-600 text-white rounded-tr-none border-indigo-500'} p-4 rounded-2xl border text-sm leading-relaxed shadow-lg">` +
                `${contentHtml}` +
                (isBot ? `<button onclick="copyToClipboard(this)" class="copy-btn" title="Copiar"><i class="far fa-copy"></i></button>` : '') +
            `</div>` +
        `</div>` +
    `</div>`;
    
    chatContainer.insertAdjacentHTML('beforeend', html);
}

function appendLoading(id) {
    const html = `<div id="${id}" class="flex gap-3 mb-6 animate-pulse">` +
        `<div class="w-8 h-8 rounded-lg bg-slate-800 flex-shrink-0 flex items-center justify-center text-slate-600 text-[10px] mt-1">` +
            `<i class="fas fa-robot"></i>` +
        `</div>` +
        `<div class="chat-bubble items-start">` +
            `<div class="bg-[#1e293b] p-4 rounded-2xl rounded-tl-none border border-slate-700 flex gap-2 items-center">` +
                `<div class="w-1.5 h-1.5 bg-indigo-500 rounded-full animate-bounce"></div>` +
                `<div class="w-1.5 h-1.5 bg-indigo-500 rounded-full animate-bounce [animation-delay:-.3s]"></div>` +
                `<div class="w-1.5 h-1.5 bg-indigo-500 rounded-full animate-bounce [animation-delay:-.5s]"></div>` +
            `</div>` +
        `</div>` +
    `</div>`;
    document.getElementById('chat-container').insertAdjacentHTML('beforeend', html);
}

function removeLoading(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

function scrollToBottom() {
    const container = document.getElementById('chat-container');
    container.scrollTop = container.scrollHeight;
}

function copyToClipboard(btn) {
    const text = btn.parentElement.innerText;
    navigator.clipboard.writeText(text).then(() => {
        const icon = btn.querySelector('i');
        icon.className = 'fas fa-check text-emerald-500';
        setTimeout(() => icon.className = 'far fa-copy', 2000);
    });
}

document.getElementById('user-input').addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        enviarPregunta();
    }
});
