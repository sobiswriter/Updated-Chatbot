const userInput = document.getElementById("user-input");
const sendButton = document.getElementById("send-button");
const uploadButton = document.getElementById("upload-button");
const fileInput = document.getElementById("file-input");
const chatMessages = document.getElementById("chat-messages");

// Fetch initial greeting when the page loads
fetch('/chat', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({message: ""})
})
.then(response => response.json())
.then(data => {
    displayMessage(data.response, "chatbot");
})
.catch(error => {
    console.error('Error fetching initial message:', error);
});

sendButton.addEventListener("click", () => sendMessage());
userInput.addEventListener("keyup", (event) => {
    if (event.key === "Enter") {
        sendMessage();
    }
});

uploadButton.addEventListener("click", () => fileInput.click());

fileInput.addEventListener("change", () => {
    if (fileInput.files.length > 0) {
        const file = fileInput.files[0];
        uploadImage(file);
    }
});

function sendMessage() {
    const message = userInput.value.trim();
    if (message !== "") {
        displayMessage("You: " + message, "user");
        userInput.value = "";

        fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message })
        })
        .then(response => response.json())
        .then(data => {
            if (data.response) {
                displayMessage(data.response, "chatbot");
            } else if (data.error) {
                displayMessage("Error: " + data.error, "error");
            } else {
                console.error('Unexpected response format:', data);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            displayMessage("Error communicating with chatbot.", "error");
        });
    }
}

function uploadImage(file) {
    const formData = new FormData();
    formData.append('file', file);

    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            displayMessage(data.message, "chatbot");
        } else if (data.error) {
            displayMessage("Error: " + data.error, "error");
        } else {
            console.error('Unexpected response format:', data);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        displayMessage("Error uploading image.", "error");
    });
}

function displayMessage(message, sender) {
    const messageElement = document.createElement("div");
    messageElement.classList.add("message", sender);

    if (sender === "chatbot") {
        messageElement.textContent = "";
        let i = 0;
        const typingInterval = setInterval(() => {
            if (i < message.length) {
                messageElement.textContent += message.charAt(i);
                i++;
            } else {
                clearInterval(typingInterval);
            }
        }, 15);
    } else {
        messageElement.textContent = message;
    }

    chatMessages.appendChild(messageElement);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}
