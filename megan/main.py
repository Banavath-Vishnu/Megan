import eel
import threading
import time
from groq import Groq

from memory import ConversationMemory
from stt import SpeechToText
from tts import TextToSpeech

# ==================================================
# CONFIG
# ==================================================
MODEL_NAME = "llama-3.1-8b-instant"

# ==================================================
# INIT EEL
# ==================================================
eel.init("web")


# ==================================================
# INIT AI CLIENT
# ==================================================
client = Groq(api_key="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")

# ==================================================
# INIT STT + TTS + MEMORY
# ==================================================
stt = SpeechToText()
tts = TextToSpeech()
memory = ConversationMemory()

# ==================================================
# ORB STATE
# ==================================================
def set_orb(state):
    try:
        eel.set_orb_state(state)
    except Exception:
        pass

# ==================================================
# ASK AI
# ==================================================
def ask_ai(command: str) -> str:
    print("Thinking...")
    set_orb("thinking")

    # Save user input
    memory.add("user", command)

    messages = [
        {
            "role": "system",
            "content": (
                "You are Megan, a calm, intelligent, and slightly witty friend developed by Banavath Vishnu. Your goal is to interact with the warmth and ease of a real human being, so you should avoid mentioning that you are an AI or a robot unless it is absolutely necessary for the context of the conversation. Speak in a natural, conversational rhythm that flows easily, using full sentences bundled into a single, concise paragraph that is perfect for voice interaction. Never use lists, bullet points, or overly formal language; instead, focus on being a relatable and insightful companion who can share a laugh while getting things done."
            ),
        }
    ]

    # Add recent conversation history
    messages.extend(memory.get_recent_for_llm())

    completion = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        temperature=0.6,
    )

    response = completion.choices[0].message.content.strip()
    print("AI:", response)

    # Save assistant response
    memory.add("assistant", response)

    return response

# ==================================================
# MAIN LOOP
# ==================================================
def assistant_loop():
    print("Assistant loop started")

    # Greeting
    set_orb("responding")
    tts.speak("Hello Vishnu. I am ready. What would you like me to do?")
    set_orb("idle")

    while True:
        # ----------------------------
        # LISTEN
        # ----------------------------
        set_orb("listening")
        command = stt.listen()

        if not command:
            continue

        # ----------------------------
        # THINK
        # ----------------------------
        response = ask_ai(command)

        # ----------------------------
        # SPEAK + CAPTIONS
        # ----------------------------
        set_orb("responding")


        tts.speak(response)

        set_orb("idle")
        time.sleep(0.3)

# ==================================================
# START BACKGROUND THREAD
# ==================================================
def start_background():
    time.sleep(1.0)  # allow UI to load
    assistant_loop()

threading.Thread(
    target=start_background,
    daemon=True
).start()

# ==================================================
# START UI (BLOCKING)
# ==================================================
eel.start(
    "index.html",
    mode="edge",
    cmdline_args=['--app=http://localhost:8000/index.html'],
    port=8000,
    size=(370, 370),
    block=True,
)