from flask import Flask, request, jsonify, send_from_directory
import vertexai
from vertexai.preview.language_models import TextGenerationModel
from vertexai.preview.generative_models import GenerativeModel, Image
from werkzeug.utils import secure_filename
import os
import random

# Vertex AI Configuration
PROJECT_ID = "x-avenue-425405-v4"
REGION = "us-central1"
vertexai.init(project=PROJECT_ID, location=REGION)

# Initialize the text generation model
text_generation_model = TextGenerationModel.from_pretrained("text-bison@001")

# Initialize the image analysis model
generative_multimodal_model = GenerativeModel("gemini-1.5-pro-001")

app = Flask(__name__, static_folder='static')

# Configuration for file uploads
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

chat_history = []  # Store conversation history

# Assistance Bot Phrases
assistance_phrases = {
    "greetings": [
        "Hello, How may I assist with your business today",
        "Hi there! What business would you like to discuss today",
        "Welcome! I humbly await your orders sir",
    ],
    "farewells": [
        "Goodbye! If you need further assistance, feel free to reach out.",
        "Take care! Let me know if I can help with anything else.",
    ],
    "thanks": [
        "You're welcome!",
        "Happy to assist!",
        "Anytime!"
    ],
    "analysis": [
        "What kind of analysis do you need help with?",
        "I can assist with data analysis, financial forecasts, and market research. What do you need?",
        "Feel free to ask about any business analysis tasks you have."
    ],
    "calculations": [
        "I can help with calculations. What would you like to compute?",
        "Need help with numbers? I'm here to assist!",
        "Let me know what calculations you need assistance with."
    ],
    "general_responses": [
        "That's an interesting query!",
        "I'm here to help with your business needs.",
        "Let me know if you have any other business-related questions."
    ]
}

conversation_started = False  # Track if the conversation has just started
initial_message_displayed = False  # Track if the initial message has been displayed
last_image_description = ""  # Store the last image description for follow-up questions


def get_chatbot_response(user_input):
    global last_image_description, conversation_started, initial_message_displayed

    chat_history.append(f"User: {user_input}")

    # Display the initial message once at the start of the session
    if not conversation_started:
        if not initial_message_displayed:
            initial_starting_message = "lets talk business"
            chatbot_response = initial_starting_message + "\n"
            initial_message_displayed = True
        else:
            chatbot_response = ""  # If the initial message has already been displayed, continue normally
        conversation_started = True
    else:
        chatbot_response = ""

    # Check for follow-up questions based on last image description
    if last_image_description and any(
        keyword in user_input.lower() for keyword in ["tell me more", "what about", "explain"]
    ):
        chatbot_response += f"You previously asked about an image. Here's what I can tell you about it: {last_image_description}."
    else:
        response = text_generation_model.predict(
            prompt=f"{''.join(chat_history)}",  # Include chat history
            temperature=0.8,
            max_output_tokens=150
        )
        chatbot_response += response.text

        # Enhanced Response Selection based on Keywords
        pre_generated_text = ""
        user_input_lower = user_input.lower()

        if any(keyword in user_input_lower for keyword in ["hello", "hi", "hey"]):
            pre_generated_text = random.choice(assistance_phrases["greetings"])
        elif any(keyword in user_input_lower for keyword in ["thank you", "thanks"]):
            pre_generated_text = random.choice(assistance_phrases["thanks"])
        elif any(keyword in user_input_lower for keyword in ["analysis", "analyze", "report"]):
            pre_generated_text = random.choice(assistance_phrases["analysis"])
        elif any(keyword in user_input_lower for keyword in ["calculate", "calculation", "compute"]):
            pre_generated_text = random.choice(assistance_phrases["calculations"])
        else:
            pre_generated_text = random.choice(assistance_phrases["general_responses"])

        if pre_generated_text:
            chatbot_response = f"{pre_generated_text}\n{chatbot_response}"

    chat_history.append(f"Chatbot: {chatbot_response}")
    return chatbot_response




# Flask Routes
@app.route('/')
def index():
    return send_from_directory('.', 'index2.html')

@app.route('/static2/<path:filename>')
def serve_static(filename):
    return send_from_directory('static2', filename)

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message')
    if user_message:
        response = get_chatbot_response(user_message)
        return jsonify({'response': response})
    else:
        initial_greeting = random.choice(assistance_phrases["greetings"])
        return jsonify({"response": initial_greeting})

@app.route('/upload', methods=['POST'])
def upload():
    global last_image_description
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected for uploading'}), 400
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        try:
            # Use Vertex AI GenerativeModel to analyze the image
            image = Image.load_from_file(filepath)
            response = generative_multimodal_model.generate_content(
                ["Tell me what you can see in the image?", image]
            )
            description = response.text
            last_image_description = description  # Store the description
            return jsonify({'message': description, 'filename': filename}), 200
        except Exception as e:
            return jsonify({'error': f'Failed to analyze image: {e}'}), 500
    else:
        return jsonify({'error': 'File not allowed'}), 400


if __name__ == '__main__':
    app.run(debug=True)
