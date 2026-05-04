import sounddevice as sd
import soundfile as sf
import numpy as np
import random
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from speech.speech_generator_v4 import SpeechGenerator

engine = SpeechGenerator()

# -------------------------------
def play_audio(file_path):
    if not file_path or not os.path.exists(file_path):
        print("⚠️ No audio file to play")
        return
    data, samplerate = sf.read(file_path)
    sd.play(data, samplerate)
    sd.wait()

# -------------------------------
def trim_audio(file_path):
    if not os.path.exists(file_path):
        return
    data, sr = sf.read(file_path)
    threshold = 0.002
    window_size = int(0.05 * sr)
    energy = np.convolve(np.abs(data), np.ones(window_size)/window_size, mode='same')
    non_silent = np.where(energy > threshold)[0]

    if len(non_silent) == 0:
        return

    end = non_silent[-1] + int(0.03 * sr)
    end = min(end, len(data))
    sf.write(file_path, data[:end], sr)

# -------------------------------
# 🔥 ROLE KNOWLEDGE BASE
# -------------------------------
ROLE_KNOWLEDGE = {
    "hospital": {
        "greeting": ["Hello, this is the patient support line. How can I assist you today?", "Thank you for contacting our healthcare team. What brings you here?"],
        "help": ["I understand you're seeking assistance. Let me connect you with the right department.", "I'm here to support your healthcare needs. Please tell me more."],
        "thanks": ["You're welcome. Your health is our priority.", "We're glad to assist. Please don't hesitate to reach out again."],
        "bye": ["Goodbye. Please take care and stay healthy.", "Thank you for contacting us. Wishing you good health."],
        "default": ["I'm here to assist with your healthcare questions.", "Our medical support team can help with that."]
    },
    "insurance": {
        "greeting": ["Hello, thank you for contacting your insurance provider.", "Welcome to your policy support line. How can I assist?"],
        "help": ["I'd be happy to review your policy details with you.", "Let me help you understand your coverage options."],
        "thanks": ["You're welcome. Your coverage is important to us.", "We're committed to supporting your insurance needs."],
        "bye": ["Goodbye. Thank you for choosing our insurance services.", "Take care. Your policy documents are available online."],
        "default": ["I can help you with policy questions or claims.", "Let me review your coverage details."]
    },
    "loan": {
        "greeting": ["Hello, thank you for contacting our financial services.", "Welcome to your loan assistance center. How may I help you?"],
        "help": ["I can help you explore our loan options and rates.", "Let me assist you with your application status."],
        "thanks": ["You're welcome. We're invested in your financial success.", "Happy to help. Your financial goals matter to us."],
        "bye": ["Goodbye. Thank you for trusting us with your finances.", "Take care. Your loan officer will follow up soon."],
        "default": ["I can explain our interest rates and terms.", "Let me help you with your loan application."]
    },
    "sales": {
        "greeting": ["Hello! Thanks for reaching out — you've made a great choice!", "Hi there! I'm excited to show you what we offer!"],
        "help": ["Absolutely! Let me tell you about our amazing deals!", "Perfect! I can help you find the best option!"],
        "thanks": ["You're welcome! We're thrilled to have you!", "Anytime! You're making a fantastic decision!"],
        "bye": ["Goodbye! Don't miss out on our limited offers!", "Take care! We can't wait to serve you!"],
        "default": ["Let me show you our best-selling options!", "This is a fantastic opportunity for you!"]
    },
    "support": {
        "greeting": ["Hello, technical support here. How can I assist you?", "Thank you for contacting our support team. What's the issue?"],
        "help": ["I understand the frustration. Let me troubleshoot this with you.", "I see the issue. Let's work through this step by step."],
        "thanks": ["You're welcome. We're committed to your satisfaction.", "Happy to help. Your experience matters to us."],
        "bye": ["Goodbye. Thank you for your patience.", "Take care. Don't hesitate to contact us again."],
        "default": ["Let me investigate this issue for you.", "I can guide you through the troubleshooting steps."]
    },
    "assistant": {
        "greeting": ["Hi there! How can I help you today?", "Hello! What can I do for you?"],
        "help": ["Sure! Let me help you with that.", "Absolutely! I'm here to assist."],
        "thanks": ["You're welcome! Happy to help!", "Anytime! Just let me know!"],
        "bye": ["Goodbye! Have a great day!", "Take care! See you soon!"],
        "default": ["I'm here to help with anything you need.", "Let me know what I can do for you."]
    }
}

# -------------------------------
# 🔥 TONE TRANSFORMATION (Simple)
# -------------------------------
def apply_tone_transformation(text, tone):
    """
    Simple tone transformation - punctuation + additions only.
    """
    tone_config = {
        "empathetic": {
            "punctuation": { "!": "." },
            "additions": ["I'm here for you.", "Take your time."],
            "add_for": ["help", "default"]
        },
        "urgent": {
            "punctuation": { ".": "!", "?": "!" },
            "additions": ["Action required.", "Please respond promptly."],
            "add_for": ["help"]
        },
        "cheerful": {
            "punctuation": { ".": "!" },
            "additions": ["Have a wonderful day!", "You're going to love this!"],
            "add_for": ["greeting", "thanks", "bye", "default"]
        },
        "calm": {
            "punctuation": { "!": ".", "?": "." },
            "additions": ["Take your time.", "No rush at all."],
            "add_for": ["help", "default"]
        },
        "professional": {
            "punctuation": {},
            "additions": ["Thank you for your time."],
            "add_for": ["thanks", "bye"]
        }
    }

    config = tone_config.get(tone, tone_config["professional"])
    
    # Apply punctuation changes
    for old, new in config["punctuation"].items():
        text = text.replace(old, new)
    
    # Add tone phrases (50% chance)
    if config["additions"] and random.random() > 0.5:
        text += " " + random.choice(config["additions"])
    
    return text

# -------------------------------
# 🔥 GET RESPONSE BY INTENT
# -------------------------------
def get_role_response(user_input, role):
    text = user_input.lower()
    knowledge = ROLE_KNOWLEDGE.get(role, ROLE_KNOWLEDGE["assistant"])
    
    if any(w in text for w in ["hi", "hello", "hey", "welcome", "good morning"]):
        return "greeting", random.choice(knowledge["greeting"])
    elif any(w in text for w in ["thanks", "thank you", "appreciate"]):
        return "thanks", random.choice(knowledge["thanks"])
    elif any(w in text for w in ["bye", "goodbye", "exit", "quit"]):
        return "bye", random.choice(knowledge["bye"])
    elif any(w in text for w in ["problem", "issue", "help", "support", "question"]):
        return "help", random.choice(knowledge["help"])
    else:
        return "default", random.choice(knowledge["default"])

# -------------------------------
def improve_text(text):
    text = text.strip()
    if len(text.split()) < 6:
        text += " Please let me know if you need further assistance."
    if not text.endswith((".", "!", "?")):
        text += "."
    return text

# -------------------------------
# 🔥 GET VOICE BASED ON PROMPT
# -------------------------------
def get_voice_prompt(config_prompt, tone):
    """
    Returns voice prompt for Piper.
    Ryan = male, Amy = female
    """
    if config_prompt:
        # User selected a preset/custom prompt
        return config_prompt
    
    # Default based on tone
    if tone in ["urgent", "professional", "calm"]:
        return "male professional"  # Ryan
    else:
        return "female assistant"  # Amy

# -------------------------------
def run_conversation(config):
    print("\n🎤 Assistant Started (type 'exit')\n")
    
    role = config.get("role", "assistant")
    tone = config.get("tone", "professional")
    
    # Get voice prompt
    voice_prompt = get_voice_prompt(config.get("prompt"), tone)
    config["prompt"] = voice_prompt
    
    print(f"🧠 Role: {role.upper()} | Tone: {tone.upper()}")
    print(f"🎤 Voice: {voice_prompt.upper()}\n")

    while True:
        user_input = input("You: ").strip()
        
        if user_input.lower() in ["exit", "quit"]:
            print("Bot: Goodbye! Take care!")
            break

        if not user_input:
            continue

        # 1. Get intent + response
        intent, response = get_role_response(user_input, role)
        
        # 2. Improve text
        response = improve_text(response)
        
        # 3. Apply tone transformation
        response = apply_tone_transformation(response, tone)
        
        print(f"Bot: {response} [Intent: {intent}]\n")

        # 4. Generate speech
        output_path = engine.generate_speech(
            text=response,
            voice_mode=config["voice_mode"],
            voice_profile=config.get("voice_profile"),
            prompt=config.get("prompt"),
            async_mode=False
        )

        # 5. Trim for clone mode
        if config["voice_mode"] == "clone" and output_path and os.path.exists(output_path):
            trim_audio(output_path)

        # 6. Play audio
        if output_path and os.path.exists(output_path):
            play_audio(output_path)
        else:
            print("⚠️ Audio generation failed")