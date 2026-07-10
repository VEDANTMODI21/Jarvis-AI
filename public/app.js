const chatBox = document.getElementById("chat-box");
const messageInput = document.getElementById("messageInput");
const sendBtn = document.getElementById("sendBtn");
const micBtn = document.getElementById("micBtn");
const historyBtn = document.getElementById("historyBtn");
const clearHistoryBtn = document.getElementById("clearHistoryBtn");
const historyPanel = document.getElementById("historyPanel");
const overlay = document.getElementById("overlay");
const statusBadge = document.getElementById("statusBadge");

let isListening = false;
let recognition = null;
let typingElement = null;

// Speech recognition setup
function initSpeechRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    showError("Speech recognition is not supported in this browser.");
    micBtn.style.display = "none";
    return;
  }

  recognition = new SpeechRecognition();
  recognition.continuous = true;
  recognition.interimResults = false;
  recognition.lang = "en-US";

  recognition.onstart = () => {
    isListening = true;
    micBtn.classList.add("active");
    statusBadge.textContent = "Listening";
    statusBadge.classList.add("listening");
  };

  recognition.onend = () => {
    const shouldRestart = isListening;
    isListening = false;
    micBtn.classList.remove("active");
    statusBadge.textContent = "Idle";
    statusBadge.classList.remove("listening");
    if (shouldRestart && recognition) {
      try { recognition.start(); } catch (e) {}
    }
  };

  recognition.onresult = (event) => {
    const transcript = event.results[event.results.length - 1][0].transcript.trim();
    console.log("Heard:", transcript);

    if (transcript.toLowerCase().startsWith("jarvis")) {
      const query = transcript.replace(/jarvis/i, "").trim();
      if (query) {
        addMessage(query, "user");
        sendMessage(query);
      } else {
        addMessage("Yes, I’m listening. What would you like?", "bot");
      }
    } else {
      // Allow direct speech input without wake word
      addMessage(transcript, "user");
      sendMessage(transcript);
    }
  };

  recognition.onerror = (event) => {
    console.error("Speech recognition error:", event.error);
    isListening = false;
    micBtn.classList.remove("active");
    statusBadge.textContent = "Idle";
    statusBadge.classList.remove("listening");
    if (event.error === "not-allowed") {
      showError("Microphone permission denied.");
    } else if (event.error === "no-speech") {
      // Silent, just restart if continuous listening
    } else {
      showError("Voice recognition error: " + event.error);
    }
  };
}

// Start / stop voice recognition
function toggleMic() {
  if (!recognition) {
    initSpeechRecognition();
  }
  if (!recognition) return;

  if (isListening) {
    recognition.stop();
  } else {
    recognition.start();
  }
}

// Send text message
function sendText() {
  const text = messageInput.value.trim();
  if (!text) return;
  addMessage(text, "user");
  messageInput.value = "";
  sendMessage(text);
}

// Dismiss the overlay after a user gesture. This satisfies browser autoplay
// policies for speech synthesis. Voice recognition is started separately via the mic button.
function initAudio() {
  overlay.style.display = "none";
}

function addMessage(text, sender) {
  const div = document.createElement("div");
  div.classList.add("message", sender);
  div.textContent = text;
  chatBox.appendChild(div);
  scrollToBottom();
}

function showTyping() {
  if (typingElement) typingElement.remove();
  typingElement = document.createElement("div");
  typingElement.classList.add("typing");
  typingElement.innerHTML = "<span></span><span></span><span></span>";
  chatBox.appendChild(typingElement);
  scrollToBottom();
}

function removeTyping() {
  if (typingElement) {
    typingElement.remove();
    typingElement = null;
  }
}

function showError(text) {
  removeTyping();
  const div = document.createElement("div");
  div.classList.add("message", "error");
  div.textContent = text;
  chatBox.appendChild(div);
  scrollToBottom();
}

function scrollToBottom() {
  chatBox.scrollTop = chatBox.scrollHeight;
}

async function sendMessage(text) {
  showTyping();

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text }),
    });

    const data = await response.json();
    removeTyping();

    if (!response.ok) {
      showError(data.error || "Something went wrong.");
      return;
    }

    typeWriter(data.response, "bot");
    speakResponse(data.response);
  } catch (err) {
    console.error("Chat error:", err);
    removeTyping();
    showError("Network error. Please try again.");
  }
}

function typeWriter(text, sender) {
  const div = document.createElement("div");
  div.classList.add("message", sender);
  chatBox.appendChild(div);
  scrollToBottom();

  let i = 0;
  const speed = 15;
  function type() {
    if (i < text.length) {
      div.textContent += text.charAt(i);
      i++;
      scrollToBottom();
      setTimeout(type, speed);
    }
  }
  type();
}

function speakResponse(text) {
  if (!window.speechSynthesis) return;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 1;
  utterance.pitch = 1;
  window.speechSynthesis.speak(utterance);
}

async function loadHistory() {
  try {
    const response = await fetch("/api/history");
    const data = await response.json();
    historyPanel.innerHTML = '<h3>Conversation History</h3>';

    if (!response.ok || !data.history || data.history.length === 0) {
      historyPanel.innerHTML += '<div class="history-empty">No history yet.</div>';
      return;
    }

    data.history.reverse().forEach((entry) => {
      const item = document.createElement("div");
      item.classList.add("history-item");
      item.innerHTML = `<div class="role">${entry.role === "user" ? "You" : "Jarvis"}</div>${escapeHtml(entry.content)}`;
      historyPanel.appendChild(item);
    });
  } catch (err) {
    console.error("History error:", err);
    historyPanel.innerHTML = '<h3>Conversation History</h3><div class="history-empty">Failed to load history.</div>';
  }
}

function toggleHistory() {
  if (historyPanel.style.display === "block") {
    historyPanel.style.display = "none";
  } else {
    historyPanel.style.display = "block";
    loadHistory();
  }
}

async function clearHistory() {
  try {
    await fetch("/api/history", { method: "DELETE" });
    loadHistory();
    chatBox.innerHTML = '<div class="empty-state">Conversation cleared. Say "Jarvis" or type a message to start.</div>';
  } catch (err) {
    console.error("Clear history error:", err);
  }
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

// Event listeners
sendBtn.addEventListener("click", sendText);
messageInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") sendText();
});
micBtn.addEventListener("click", toggleMic);
historyBtn.addEventListener("click", toggleHistory);
clearHistoryBtn.addEventListener("click", clearHistory);
overlay.addEventListener("click", initAudio);

// Initial empty state
if (!chatBox.children.length) {
  chatBox.innerHTML = '<div class="empty-state">Say "Jarvis" or type a message to start.</div>';
}
