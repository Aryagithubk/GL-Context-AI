const form = document.getElementById('query-form');
const input = document.getElementById('query-input');
const chatContainer = document.getElementById('chat-container');
const loader = document.getElementById('loader');

// Suggestion chips
document.querySelectorAll('.suggestion-chip').forEach(chip => {
    chip.addEventListener('click', () => {
        input.value = chip.textContent;
        form.dispatchEvent(new Event('submit'));
    });
});

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const query = input.value.trim();
    if (!query) return;

    // Remove welcome message
    const welcome = document.querySelector('.welcome-message');
    if (welcome) welcome.remove();

    // Show user message
    appendMessage(query, 'user');
    input.value = '';
    loader.style.display = 'flex';

    try {
        const res = await fetch('/api/v1/query', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query })
        });

        const data = await res.json();
        appendMessage(
            data.answer,
            'bot',
            data.sources || [],
            data.agents_used || [],
            data.confidence || 0
        );
    } catch (err) {
        console.error('Query error:', err);
        appendMessage('⚠️ Sorry, I couldn\'t reach the server. Please ensure the backend is running on port 8000.', 'bot');
    } finally {
        loader.style.display = 'none';
    }
});

function appendMessage(text, sender, sources = [], agentsUsed = [], confidence = 0) {
    const msgDiv = document.createElement('div');
    msgDiv.classList.add('message', sender);

    const avatar = document.createElement('div');
    avatar.classList.add('avatar');
    avatar.textContent = sender === 'user' ? '👤' : '✨';

    const contentDiv = document.createElement('div');
    contentDiv.classList.add('message-content');

    const textDiv = document.createElement('div');
    textDiv.classList.add('text');
    textDiv.innerHTML = formatText(text);
    contentDiv.appendChild(textDiv);

    if (sender === 'bot') {
        // ── Agent badges ──
        if (agentsUsed.length > 0) {
            const agentsDiv = document.createElement('div');
            agentsDiv.classList.add('agents-used');
            agentsDiv.innerHTML = agentsUsed.map(agent => {
                const icon = getAgentIcon(agent);
                const cls = getAgentClass(agent);
                return `<span class="agent-badge ${cls}">${icon} ${agent}</span>`;
            }).join('');

            // Confidence indicator
            if (confidence > 0) {
                const pct = Math.round(confidence * 100);
                const level = confidence >= 0.7 ? 'high' : confidence >= 0.4 ? 'med' : 'low';
                agentsDiv.innerHTML += `<span class="confidence-badge confidence-${level}">${pct}% confidence</span>`;
            }

            contentDiv.appendChild(agentsDiv);
        }

        // ── Source citations ──
        if (sources.length > 0) {
            const sourcesDiv = document.createElement('div');
            sourcesDiv.classList.add('sources');
            sourcesDiv.innerHTML = 'Sources: ' + sources.map(s => {
                const icon = getSourceIcon(s.source_type);
                const name = getSourceName(s);
                const cls = getSourceClass(s.source_type);
                return `<span class="source-tag ${cls}">${icon} ${name}</span>`;
            }).join('');
            contentDiv.appendChild(sourcesDiv);
        }
    }

    msgDiv.appendChild(avatar);
    msgDiv.appendChild(contentDiv);
    chatContainer.appendChild(msgDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function getAgentIcon(agent) {
    const icons = {
        'DocAgent': '📄',
        'DBAgent': '🗄️',
        'ConfluenceAgent': '📖',
        'WebSearchAgent': '🌐',
        'Fallback': 'ℹ️',
    };
    return icons[agent] || '🤖';
}

function getAgentClass(agent) {
    const classes = {
        'DocAgent': 'agent-doc',
        'DBAgent': 'agent-db',
        'ConfluenceAgent': 'agent-confluence',
        'WebSearchAgent': 'agent-web',
        'Fallback': 'agent-fallback',
    };
    return classes[agent] || '';
}

function getSourceIcon(type) {
    const icons = {
        'document': '📄',
        'database': '🗄️',
        'confluence': '📖',
        'web': '🌐',
        'general_knowledge': 'ℹ️',
    };
    return icons[type] || '📎';
}

function getSourceClass(type) {
    const classes = {
        'document': 'source-doc',
        'database': 'source-db',
        'confluence': 'source-confluence',
        'web': 'source-web',
        'general_knowledge': 'source-general',
    };
    return classes[type] || '';
}

function getSourceName(source) {
    if (source.source_type === 'document') {
        const path = source.source_identifier || 'Unknown';
        return path.split('\\').pop().split('/').pop();
    }
    if (source.source_type === 'database') {
        return source.excerpt || 'Database Query';
    }
    if (source.source_type === 'web') {
        try {
            return new URL(source.source_identifier).hostname;
        } catch {
            return 'Web Source';
        }
    }
    if (source.source_type === 'confluence') {
        return 'Confluence Page';
    }
    return source.source_identifier || 'Unknown';
}

function formatText(text) {
    if (!text) return '';
    return text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/\n/g, '<br>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/`(.*?)`/g, '<code>$1</code>');
}
