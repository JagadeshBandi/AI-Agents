const apiBase = 'http://localhost:8000';
const logElement = document.getElementById('extensionLog');
const form = document.getElementById('extensionForm');

function appendLog(text) {
    const now = new Date().toLocaleTimeString();
    logElement.textContent += `\n[${now}] ${text}`;
    logElement.scrollTop = logElement.scrollHeight;
}

async function connectWebSocket(sessionId) {
    const ws = new WebSocket(`ws://localhost:8000/ws/agents/${sessionId}`);

    ws.onopen = () => appendLog('WebSocket connected.');
    ws.onmessage = (event) => {
        try {
            const payload = JSON.parse(event.data);
            if (payload.type === 'log') {
                appendLog(payload.message);
            }
        } catch (err) {
            appendLog('WebSocket parse error: ' + err.message);
        }
    };
    ws.onclose = () => appendLog('WebSocket closed.');
    ws.onerror = (err) => appendLog('WebSocket error.');
}

form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const payload = {
        profile: {
            name: document.getElementById('name').value,
            email: document.getElementById('email').value,
            linkedin: '',
            github: '',
            resume_text: document.getElementById('resumeText').value,
        },
        preferences: {
            keywords: document.getElementById('keywords').value,
            location: document.getElementById('location').value,
            country: document.getElementById('country').value.toUpperCase(),
            minimum_salary: 30000,
                humanizer: document.getElementById('humanizer').value,
            appendLog('Failed to start pipeline: ' + errorText);
            return;
        }

        const data = await response.json();
        appendLog('Pipeline started: session=' + data.session_id);
        connectWebSocket(data.session_id);
    } catch (error) {
        appendLog('Network error: ' + error.message);
    }
});
