// Register the service worker
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js')
        .then(reg => console.log('Service worker registered', reg))
        .catch(err => console.log('Service worker not registered', err));
}

// Get our DOM elements
const chatContainer = document.getElementById('chat-container');
const queryInput = document.getElementById('queryInput');
const askButton = document.getElementById('askButton');

/**
 * Adds a message to the chat window.
 * @param {string} content - The HTML content of the message.
 * @param {string} sender - 'user' or 'ai'.
 * @returns {HTMLElement} - The div containing the message content.
 */
function addMessage(content, sender) {
    // 1. Create the main message bubble
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', `${sender}-message`);

    // 2. Create the content element
    const contentDiv = document.createElement('div');
    contentDiv.classList.add('message-content');
    contentDiv.innerHTML = content;

    // 3. Create the timestamp
    const timeString = new Date().toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
    const timestampDiv = document.createElement('div');
    timestampDiv.classList.add('timestamp');
    timestampDiv.textContent = timeString;

    // 4. Add content and timestamp to the bubble
    messageDiv.appendChild(contentDiv);
    messageDiv.appendChild(timestampDiv);
    
    // 5. Add the bubble to the chat
    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;

    // 6. Return the content div so we can update it (for loading messages)
    return contentDiv;
}

// Handle the "ask" button click
async function handleAsk() {
    const query = queryInput.value;
    if (!query) return; // Don't send empty messages

    // 1. Add the user's message
    addMessage(query, 'user');
    queryInput.value = ''; // Clear the input

    // --- Start Timer ---
    const startTime = Date.now();

    // 2. Add a temporary loading message and get its content area
    const loadingContent = addMessage(
        `<div class="loading">Council is thinking...</div>`, 
        'ai'
    );

    try {
        // 3. Call the Rust backend
        const response = await fetch("http://localhost:8080/api/council", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ query: query })
        });

        // --- End Timer ---
        const endTime = Date.now();
        const duration = ((endTime - startTime) / 1000).toFixed(2); // Duration in seconds

        if (!response.ok) {
            throw new Error(`Server error: ${response.statusText}`);
        }

        const data = await response.json();

        // 4. Build the AI's response content, now with the timer
        let aiResponseHtml = `
            <div class="response-time">Responded in ${duration} seconds</div>
            ${data.final_answer.replace(/\n/g, '<br>')}
            <div class="council-work">
                <strong>Council Deliberations:</strong>
        `;

        // Loop through the individual model answers
        data.model_answers.forEach((item, index) => {
            aiResponseHtml += `
                <p>
                    <strong>${item.model} (${index + 1}):</strong> 
                    ${item.answer.replace(/\n/g, '<br>')}
                </p>
            `;
        });
        
        aiResponseHtml += '</div>';

        // 5. Update the loading message's content with the final response
        loadingContent.innerHTML = aiResponseHtml;

    } catch (err) {
        // 6. If an error happens, update the loading message
        loadingContent.innerHTML = `Error: Could not connect to the AI council. <br>(${err.message})`;
        loadingContent.parentElement.style.backgroundColor = '#ffdddd'; // Target the parent bubble
        loadingContent.parentElement.style.color = '#d8000c';
    }
}

// Add event listeners
askButton.addEventListener("click", handleAsk);
queryInput.addEventListener("keypress", function(event) {
    if (event.key === "Enter") {
        handleAsk();
    }
});