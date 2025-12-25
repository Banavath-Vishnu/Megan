import eel
import threading
import time
from groq import Groq

from memory import ConversationMemory
from stt import SpeechToText
from tts import TextToSpeech

import json
from tavily import TavilyClient

tavily = TavilyClient(api_key="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")


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
# Fetch WEB INFO
# ==================================================
def fetch_web_info(query: str) -> str:
    result = tavily.search(query=query, max_results=3)
    return "\n".join(r["content"] for r in result.get("results", []))

# ==================================================
# TOOLS
# ==================================================
TOOLS = [{
    "type": "function",
    "function": {
        "name": "fetch_web_info",
        "description": "Get real-time information from the web",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string"}
            },
            "required": ["query"]
        }
    }
}]



# ==================================================
# ASK AI
# ==================================================

def ask_ai(command: str) -> str:
    print("Thinking...")
    set_orb("thinking")

    # Save user input
    memory.add("user", command)

    # Prepare message history
    messages = [
        {
            "role": "system",
            "content": (
                "You are Megan, a calm, intelligent, and slightly witty friend developed by Banavath Vishnu. "
                "Interact naturally. If you need information you don't have, use the search tool. "
                "Respond in a single, concise paragraph suitable for voice interaction."
            ),
        }
    ]
    messages.extend(memory.get_recent_for_llm())

    # --- STEP 1: Initial Request to AI ---
    completion = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        temperature=0.6,
        tools=TOOLS,
        tool_choice="auto",
    )

    response_message = completion.choices[0].message
    
    # --- STEP 2: Check if AI wants to use a tool ---
    if response_message.tool_calls:
        # 1. Add the assistant's request to the message history
        messages.append(response_message)
        
        # 2. Process each tool call the AI requested
        for tool_call in response_message.tool_calls:
            if tool_call.function.name == "fetch_web_info":
                # Parse arguments
                args = json.loads(tool_call.function.arguments)
                search_query = args.get("query")
                
                # Execute the actual search
                print(f"Searching for: {search_query}...")
                search_result = fetch_web_info(search_query)
                
                # 3. Add the search result back to history with role "tool"
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": "fetch_web_info",
                    "content": search_result,
                })

        # --- STEP 3: Second Request to AI (to summarize search results) ---
        final_completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
        )
        final_response = final_completion.choices[0].message.content.strip()
    else:
        # No tool used, just use the normal response
        final_response = response_message.content.strip()

    print("AI:", final_response)
    memory.add("assistant", final_response)

    return final_response
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