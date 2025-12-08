let isListening = false;
let recognition;
const chatBox = document.getElementById("chat-box");
const historyContainer = document.getElementById("historyContainer");
const historyBtn = document.getElementById("historyBtn");

// Function to initialize the speech recognition
function initAudio() {
    document.getElementById("overlay").style.display = "none";
    startRecognition();
}

// Initialize Speech Recognition
if ('webkitSpeechRecognition' in window) {
    recognition = new webkitSpeechRecognition();
} else {
    recognition = new SpeechRecognition();
}

recognition.continuous = true;  // Allow continuous listening
recognition.lang = "en-US";
recognition.interimResults = false; // Only process finished results

recognition.onresult = function (event) {
    const transcript = event.results[event.results.length - 1][0].transcript.toLowerCase().trim();
    console.log("Heard:", transcript);  // Log the transcript for debugging

    if (transcript.includes("jarvis")) {
        const query = transcript.replace("jarvis", "").trim(); // Extract the command
        if (query) {
            appendMessage("You: " + query, "user");  // Display user input
            appendMessage("Jarvis is processing your request...", "bot");  // Processing message
            getBotResponse(query);  // Get bot response
        }
    }
};

// Restart recognition if it stops
recognition.onend = function () {
    if (isListening) {
        recognition.start();
    }
};

// Handle any errors during recognition
recognition.onerror = function (event) {
    console.error("Speech Recognition Error:", event.error);
};

// Start recognition
function startRecognition() {
    isListening = true;
    recognition.start();
}

// Append messages to the chat container
function appendMessage(message, sender) {
    const messageDiv = document.createElement("div");
    messageDiv.classList.add("message", sender);
    messageDiv.textContent = message;
    chatBox.appendChild(messageDiv);
    chatBox.scrollTop = chatBox.scrollHeight;  // Auto scroll to the latest message
}

// Get bot response from the backend
function getBotResponse(query) {
    fetch("/process", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: query })
    })
    .then(response => response.json())
    .then(data => {
        let botResponse = data.response;
        appendTypingEffect(botResponse); // Show the bot response with typing effect
        speakResponse(botResponse); // Speak the bot response
    })
    .catch(err => {
        console.error("Error fetching bot response:", err);
    });
}

// Add typing effect to the bot's response
function appendTypingEffect(message) {
    let index = 0;
    let interval = setInterval(() => {
        if (index < message.length) {
            appendMessage(message.substring(0, index + 1), "bot");
            index++;
        } else {
            clearInterval(interval);  // Stop typing effect when finished
        }
    }, 100);  // Speed of typing effect
}

// Speak the bot's response using Speech Synthesis
function speakResponse(response) {
    const synth = window.speechSynthesis;
    const utterance = new SpeechSynthesisUtterance(response);
    utterance.rate = 1;  // Adjust speech rate
    synth.speak(utterance);
}

// Display chat history when the history button is clicked
historyBtn.addEventListener("click", function () {
    fetch("/history")
        .then(res => res.json())
        .then(data => {
            historyContainer.innerHTML = "";
            historyContainer.style.display = "block";
            if (data.history.length === 0) {
                historyContainer.innerHTML = "<p>No history found.</p>";
            } else {
                data.history.forEach(entry => {
                    const userDiv = document.createElement("div");
                    userDiv.classList.add("message", "user");
                    userDiv.textContent = "You: " + entry.user_query;

                    const botDiv = document.createElement("div");
                    botDiv.classList.add("message", "bot");
                    botDiv.textContent = "Jarvis: " + entry.bot_response;

                    historyContainer.appendChild(userDiv);
                    historyContainer.appendChild(botDiv);
                });
            }
        })
        .catch(err => {
            console.error("Failed to load history", err);
        });
});
