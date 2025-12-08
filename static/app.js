let isListening = false;
let recognition;
const chatBox = document.getElementById("chat-box");
const historyContainer = document.getElementById("historyContainer");
const historyBtn = document.getElementById("historyBtn");

function initAudio() {
  // Hide the overlay
  document.getElementById("overlay").style.display = "none";
  startRecognition();  // Start recognition when clicked
}

if ('webkitSpeechRecognition' in window) {
  recognition = new webkitSpeechRecognition();
} else {
  recognition = new SpeechRecognition();
}

recognition.continuous = true;
recognition.lang = "en-US";

recognition.onresult = async function(event) {
  const transcript = event.results[event.results.length - 1][0].transcript.toLowerCase().trim();
  console.log("Heard:", transcript);

  if (transcript.includes("jarvis")) {
    const query = transcript.replace("jarvis", "").trim();
    if (query) {
      appendMessage("You: " + query, "user");
      getBotResponse(query);
    }
  }
};

recognition.onerror = function(event) {
  console.error("Speech Recognition Error:", event.error);
};

recognition.onend = function() {
  if (isListening) recognition.start();  // Restart recognition if it stops
};

function startRecognition() {
  isListening = true;
  recognition.start();
}

function appendMessage(message, sender) {
  const messageDiv = document.createElement("div");
  messageDiv.classList.add("message", sender);
  messageDiv.textContent = message;
  chatBox.appendChild(messageDiv);
  chatBox.scrollTop = chatBox.scrollHeight;
}

async function getBotResponse(query) {
  const response = await fetch("/process", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: query })
  });
  const data = await response.json();
  appendMessage("Jarvis: " + data.response, "bot");
}

historyBtn.addEventListener("click", function() {
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
    });
});
