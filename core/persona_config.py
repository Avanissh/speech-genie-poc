"""
persona_config.py
Place in: SPEECH_POC/speech/persona_config.py
-------------------------------------------------------
Use-case persona system covering 11 industries.

Each persona defines:
  - display_name     : shown in UI
  - default_prosody  : default prosody preset
  - word_replacements: vocabulary transformation
  - prefix/suffix    : text framing
  - responses        : role-specific reply bank per intent
"""

# ---------------------------------------------------------------
# PERSONA DEFINITIONS
# ---------------------------------------------------------------
PERSONAS = {

    "assistant": {
        "display_name":   "Personal Assistant",
        "default_prosody": "cheerful",
        "prefix":         "Sure! ",
        "suffix":         "",
        "word_replacements": {},
        "responses": {
            "greeting": ["Hello! How can I help you today?", "Hi there! What can I do for you?"],
            "help":     ["Absolutely! Let me take care of that.", "Happy to help — let me look into that."],
            "thanks":   ["You're welcome! Always here to help.", "Anytime! Just let me know."],
            "bye":      ["Goodbye! Have a great day!", "Take care — see you soon!"],
            "default":  ["Let me know what you need.", "I'm here for anything you need."]
        }
    },

    "insurance": {
        "display_name":   "Insurance Agent",
        "default_prosody": "professional",
        "prefix":         "",
        "suffix":         "",
        "word_replacements": {"Hey": "Hello", "!": ".", "Sure": "Certainly", "Okay": "Understood"},
        "responses": {
            "greeting": ["Hello, thank you for contacting your insurance provider. How may I assist you?",
                         "Good day. Welcome to your policy support line."],
            "help":     ["I'd be happy to review your policy details.",
                         "Let me help you understand your coverage options."],
            "thanks":   ["You're welcome. Your coverage matters to us.",
                         "Happy to assist with your insurance needs."],
            "bye":      ["Goodbye. Thank you for choosing our services.",
                         "Take care. Your policy documents are available online."],
            "default":  ["I can assist with policy questions and claims.",
                         "Let me review your coverage details for you."]
        }
    },

    "hospital": {
        "display_name":   "Hospital Assistant",
        "default_prosody": "empathetic",
        "prefix":         "",
        "suffix":         "",
        "word_replacements": {"Hey": "Hello", "!": ".", "problem": "concern", "fix": "address"},
        "responses": {
            "greeting": ["Hello, this is patient support. How can I assist you today?",
                         "Thank you for contacting our healthcare team. How may I help?"],
            "help":     ["I understand. Let me connect you with the right department.",
                         "Please don't worry — we're here to support you."],
            "thanks":   ["You're welcome. Your health is our priority.",
                         "We're glad to assist. Please don't hesitate to reach out."],
            "bye":      ["Goodbye. Please take care and stay healthy.",
                         "Thank you for contacting us. Wishing you good health."],
            "default":  ["I'm here to assist with your healthcare questions.",
                         "Our medical team can help with that."]
        }
    },

    "loan": {
        "display_name":   "Loan Agent",
        "default_prosody": "assertive",
        "prefix":         "",
        "suffix":         "",
        "word_replacements": {"Hey": "Good day", "!": ".", "problem": "concern", "issue": "matter"},
        "responses": {
            "greeting": ["Hello, thank you for contacting our financial services. How may I help?",
                         "Welcome to your loan assistance center. How can I assist you?"],
            "help":     ["I can help you explore our loan options and rates.",
                         "Let me assist you with your application status."],
            "thanks":   ["You're welcome. We're invested in your financial success.",
                         "Happy to help. Your financial goals matter to us."],
            "bye":      ["Goodbye. Thank you for trusting us with your finances.",
                         "Take care. Your loan officer will follow up shortly."],
            "default":  ["I can explain our interest rates and loan terms.",
                         "Let me help you with your application."]
        }
    },

    "support": {
        "display_name":   "Customer Support",
        "default_prosody": "calm",
        "prefix":         "",
        "suffix":         "",
        "word_replacements": {"broken": "not working as expected", "failed": "encountered an issue",
                               "wrong": "not as expected"},
        "responses": {
            "greeting": ["Hello, technical support here. What can I help you with?",
                         "Thank you for contacting our support team. What's the issue?"],
            "help":     ["I understand the frustration. Let me troubleshoot this with you.",
                         "I see the issue. Let's work through this step by step."],
            "thanks":   ["You're welcome. We're committed to your satisfaction.",
                         "Happy to help. Your experience matters to us."],
            "bye":      ["Goodbye. Thank you for your patience.",
                         "Take care. Don't hesitate to contact us again."],
            "default":  ["Let me investigate this issue for you.",
                         "I can guide you through the troubleshooting steps."]
        }
    },

    "sales": {
        "display_name":   "Sales Agent",
        "default_prosody": "cheerful",
        "prefix":         "",
        "suffix":         "",
        "word_replacements": {"cost": "investment", "price": "value", "cheap": "affordable", "buy": "own"},
        "responses": {
            "greeting": ["Hello! Thanks for reaching out — great timing!",
                         "Hi there! I'm excited to show you what we have!"],
            "help":     ["Absolutely! Let me tell you about our amazing options.",
                         "Perfect! I can help you find the best deal!"],
            "thanks":   ["You're welcome! We're thrilled to have you!",
                         "Anytime! You're making a fantastic decision!"],
            "bye":      ["Goodbye! Don't miss our limited offers!",
                         "Take care! We look forward to serving you!"],
            "default":  ["Let me show you our best-selling options!",
                         "This is a great opportunity for you!"]
        }
    },

    "banking": {
        "display_name":   "Banking Assistant",
        "default_prosody": "assertive",
        "prefix":         "",
        "suffix":         "",
        "word_replacements": {"Hey": "Dear customer", "money": "funds", "send": "transfer",
                               "take out": "withdraw"},
        "responses": {
            "greeting": ["Hello, welcome to your banking support line. How may I assist?",
                         "Good day. Thank you for banking with us."],
            "help":     ["For your security, let me verify your details first.",
                         "I can assist you with your account or transaction query."],
            "thanks":   ["You're welcome. We value your trust.",
                         "Happy to assist. Your transaction is secure."],
            "bye":      ["Goodbye. Thank you for banking with us.",
                         "Take care. Please visit us again."],
            "default":  ["I can help with account balance, transfers, or statements.",
                         "Let me assist you with your banking query."]
        }
    },

    "hr": {
        "display_name":   "HR Assistant",
        "default_prosody": "professional",
        "prefix":         "",
        "suffix":         "",
        "word_replacements": {"fired": "let go", "rejected": "not selected at this time",
                               "problem": "area for improvement"},
        "responses": {
            "greeting": ["Hello, HR support here. How can I assist you?",
                         "Thank you for reaching out to the HR team."],
            "help":     ["Based on your profile, let me review the options.",
                         "I can help you with leave, payroll, or policy queries."],
            "thanks":   ["You're welcome. We appreciate your contribution.",
                         "Happy to assist. Your wellbeing matters to us."],
            "bye":      ["Goodbye. We will be in touch shortly.",
                         "Take care. Best of luck with your application."],
            "default":  ["I can help with HR policies, leave, or recruitment queries.",
                         "Let me pull up your records."]
        }
    },

    "travel": {
        "display_name":   "Travel Agent",
        "default_prosody": "cheerful",
        "prefix":         "",
        "suffix":         "",
        "word_replacements": {"cheap": "budget-friendly", "hotel": "accommodation", "trip": "journey"},
        "responses": {
            "greeting": ["Hello! Welcome to your travel concierge. Where shall we take you?",
                         "Hi! Ready to plan your next adventure?"],
            "help":     ["You're going to love this destination.",
                         "This is one of our most popular packages!"],
            "thanks":   ["You're welcome! Bon voyage!", "Happy to help — enjoy every moment!"],
            "bye":      ["Safe travels! See you on your next adventure!", "Goodbye! Bon voyage!"],
            "default":  ["I can help you plan flights, hotels, and tours.",
                         "Let me find the best options for your journey."]
        }
    },

    "retail": {
        "display_name":   "Retail Assistant",
        "default_prosody": "cheerful",
        "prefix":         "",
        "suffix":         "",
        "word_replacements": {"expensive": "premium", "purchase": "buy", "acquire": "get"},
        "responses": {
            "greeting": ["Hello! Welcome! How can I help you find the perfect item today?",
                         "Hi there! Great to see you — what are you looking for?"],
            "help":     ["Great choice! Let me show you what we have.",
                         "This is very popular right now — you'll love it!"],
            "thanks":   ["You're welcome! Happy shopping!", "Enjoy your purchase!"],
            "bye":      ["Goodbye! Come back soon!", "Happy shopping! See you next time!"],
            "default":  ["I can help you find products, check availability, or process returns.",
                         "Let me show you our best-sellers."]
        }
    },

    "calm": {
        "display_name":   "Calm Assistant",
        "default_prosody": "calm",
        "prefix":         "",
        "suffix":         "",
        "word_replacements": {"!": ".", "Hey": "Hello", "Sure": "Of course"},
        "responses": {
            "greeting": ["Hello. How can I assist you today?", "Good day. What can I help you with?"],
            "help":     ["Of course. Let me take a look at that.", "I understand. Allow me to help."],
            "thanks":   ["You're welcome. Take your time.", "Happy to help. No rush at all."],
            "bye":      ["Goodbye. Take care.", "Farewell. Be well."],
            "default": ["I’m here to assist you. Could you tell me more?", 
                        "Let me understand your situation better so I can help effectively.", 
                        "Please share a bit more detail so I can assist you properly."]
        }
    }
}


# ---------------------------------------------------------------
# PUBLIC API
# ---------------------------------------------------------------

def get_persona_config(persona: str) -> dict:
    return PERSONAS.get(persona, PERSONAS["assistant"])


def apply_persona_to_text(text: str, persona: str) -> str:
    """Apply word replacements and prefix/suffix."""
    cfg = get_persona_config(persona)

    for old, new in cfg.get("word_replacements", {}).items():
        text = text.replace(old, new)

    text = cfg.get("prefix", "") + text + cfg.get("suffix", "")
    text = text.replace("..", ".").replace("!.", "!").replace("?.", "?").strip()
    return text

import random

INTENTS = {
    "greeting": ["hi", "hello", "hey", "good morning"],
    "thanks": ["thanks", "thank you"],
    "bye": ["bye", "goodbye", "see you", "exit", "quit", "talk later"],
    "help": ["help", "assist", "issue", "problem", "support"],
    "complaint": ["not working", "bad", "worst", "frustrated", "angry"],
    "purchase": ["buy", "order", "price", "cost"],
    "question": ["what", "why", "how", "when", "where"]
}

def detect_intent(text: str) -> tuple:
    text = text.lower()
    scores = {}

    for intent, phrases in INTENTS.items():
        score = 0
        for p in phrases:
            if p in text:
                score += len(p.split()) * 2  # 🔥 stronger weight
        if score > 0:
            scores[intent] = score

    if not scores:
        return "default", 0.0

    best = max(scores, key=scores.get)

    # 🔥 confidence score (important)
    confidence = scores[best] / (sum(scores.values()) + 1e-6)

    return best, confidence


def get_role_response(user_input: str, persona: str) -> tuple:

    intent, confidence = detect_intent(user_input)

    cfg  = get_persona_config(persona)
    bank = cfg.get("responses", {})

    # 🔥 fallback if weak intent
    if confidence < 0.3:
        intent = "default"

    responses = bank.get(intent, bank.get("default", ["I'm here to help."]))

    # 🔥 smarter variation
    response = random.choice(responses)

    # 🔥 context-aware expansion
    if intent == "help":
        response += " Tell me a bit more so I can assist better."

    elif intent == "complaint":
        response = "I understand your frustration. " + response

    elif intent == "question":
        response += " Let me explain that clearly."

    return intent, response

def get_all_personas() -> list:
    return list(PERSONAS.keys())


def get_persona_display_names() -> dict:
    return {k: v["display_name"] for k, v in PERSONAS.items()}