import asyncio
import edge_tts
import pygame
import eel
import os
import uuid
import time
from dotenv import load_dotenv

load_dotenv()

VOICE = os.getenv("AssistantVoice", "en-US-AriaNeural")
RATE = "+20%"
PITCH = "+3Hz"


class TextToSpeech:
    def __init__(self):
        pygame.mixer.init()
        self.audio_file = None

    async def _generate_tts(self, text: str):
        """
        Generate MP3 audio and timed word boundaries
        """
        communicate = edge_tts.Communicate(
            text=text,
            voice=VOICE,
            rate=RATE,
            pitch=PITCH,
        )

        audio_bytes = b""
        words = []

        async for event in communicate.stream():
            if event["type"] == "audio":
                audio_bytes += event["data"]

            elif event["type"] == "WordBoundary":
                words.append({
                    "word": event["text"],
                    "time": event["offset"] / 10_000_000  # seconds
                })

        audio_file = f"tts_{uuid.uuid4().hex}.mp3"
        with open(audio_file, "wb") as f:
            f.write(audio_bytes)

        return audio_file, words

    def speak(self, text: str):
        if not text.strip():
            return

        eel.clear_captions()

        # --- Generate audio + timing ---
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            audio_file, words = loop.run_until_complete(
                self._generate_tts(text)
            )
        finally:
            loop.close()

        # --- Play audio ---
        pygame.mixer.music.load(audio_file)
        pygame.mixer.music.play()

        start_time = time.perf_counter()
        last_index = 0

        # --- Word-by-word captions (TRUE sync) ---
        for item in words:
            target_time = item["time"]

            # Wait until the word is actually spoken
            while time.perf_counter() - start_time < target_time:
                time.sleep(0.002)

            eel.clear_captions()           # 👈 ONLY ONE WORD VISIBLE
            eel.update_caption(item["word"])

            last_index += 1

            if not pygame.mixer.music.get_busy():
                break

        # Wait until audio ends
        while pygame.mixer.music.get_busy():
            time.sleep(0.01)

        pygame.mixer.music.stop()
        pygame.mixer.music.unload()

        try:
            os.remove(audio_file)
        except Exception:
            pass
