const form = document.getElementById('query-form');
const input = document.getElementById('query-input');
const chatContainer = document.getElementById('chat-container');
const loader = document.getElementById('loader');
const sendBtn = document.getElementById('send-btn');
const welcomeMessage = document.querySelector('.welcome-message');

// Handle Suggestion Chips
document.querySelectorAll('.suggestion-chip').forEach(chip => {
    chip.addEventListener('click', () => {
        input.value = chip.innerText;
        submitQuery();
    });
});

form.addEventListener('submit', (e) => {
    e.preventDefault();
    submitQuery();
});

async function submitQuery() {
    const query = input.value.trim();
    if (!query) return;

    // UI Updates
    if (welcomeMessage) welcomeMessage.style.display = 'none';
    appendMessage(query, 'user');
    input.value = '';
    input.disabled = true;
    sendBtn.disabled = true;
    loader.style.display = 'flex';

    // Scroll to bottom
    scrollToBottom();

    try {
        const response = await fetch('/query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query: query }),
        });

        if (!response.ok) {
            throw new Error('Network response was not ok');
        }

        const data = await response.json();
        appendMessage(data.answer, 'bot', data.sources, data.source_type);

    } catch (error) {
        console.error('Error:', error);
        appendMessage("Sorry, I couldn't reach the server. Please ensure the backend is running.", 'bot');
    } finally {
        input.disabled = false;
        sendBtn.disabled = false;
        loader.style.display = 'none';
        input.focus();
        scrollToBottom();
    }
}

// On Load: Fetch Context
window.addEventListener('load', async () => {
    try {
        const response = await fetch('/context');
        const data = await response.json();
        const greetingElement = document.getElementById('dynamic-greeting');
        if (data.summary) {
            greetingElement.innerText = `I can help you with: ${data.summary}`;
        } else {
            greetingElement.innerText = "I'm your corporate knowledge assistant. How can I help you today?";
        }
    } catch (error) {
        console.error("Failed to load context:", error);
    }
});

function appendMessage(text, sender, sources = [], sourceType = 'db') {
    const msgDiv = document.createElement('div');
    msgDiv.classList.add('message', sender);

    const avatar = document.createElement('div');
    avatar.classList.add('avatar');
    avatar.innerText = sender === 'user' ? '👤' : '✨';

    const contentDiv = document.createElement('div');
    contentDiv.classList.add('message-content');

    // Parse markdown-like bolding for simple display
    const formattedText = text.replace(/\n/g, '<br>');
    contentDiv.innerHTML = formattedText;

    if (sources && sources.length > 0) {
        const sourcesDiv = document.createElement('div');
        sourcesDiv.classList.add('sources');

        // Add Source Badge (DB vs Web)
        const badgeClass = sourceType === 'web' ? 'badge-web' : 'badge-db';
        const badgeLabel = sourceType === 'web' ? '🌐 Web Search' : '📂 Knowledge Base';

        let sourcesHtml = `<span class="source-badge ${badgeClass}">${badgeLabel}</span> `;

        sourcesHtml += sources.map(s => {
            if (s === "Web Search") return "";
            const filename = s.split('\\').pop().split('/').pop();
            return `<span class="source-tag">📄 ${filename}</span>`;
        }).join('');

        sourcesDiv.innerHTML = sourcesHtml;
        contentDiv.appendChild(sourcesDiv);
    }

    msgDiv.appendChild(avatar);
    msgDiv.appendChild(contentDiv);

    chatContainer.appendChild(msgDiv);
}

function scrollToBottom() {
    chatContainer.scrollTop = chatContainer.scrollHeight;
}
