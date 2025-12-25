# import asyncio
# import os
# import uuid
# import pygame
# import edge_tts
# from dotenv import load_dotenv

# # --------------------------------------------------
# # LOAD CONFIG
# # --------------------------------------------------
# load_dotenv()

# VOICE = os.getenv("AssistantVoice", "en-US-AriaNeural")

# # Tune these for personality
# PITCH = "+4Hz"
# RATE = "+25%"   # faster speech for responsiveness

# # --------------------------------------------------
# # TEXT TO SPEECH CLASS
# # --------------------------------------------------
# class TextToSpeech:
#     def __init__(self):
#         # Initialize pygame mixer once
#         pygame.mixer.init()

#     # --------------------------------------------------
#     # INTERNAL: TEXT -> AUDIO FILE
#     # --------------------------------------------------
#     async def _text_to_audio(self, text: str, file_path: str):
#         communicate = edge_tts.Communicate(
#             text=text,
#             voice=VOICE,
#             pitch=PITCH,
#             rate=RATE,
#         )
#         await communicate.save(file_path)

#     # --------------------------------------------------
#     # INTERNAL: PLAY AUDIO FILE
#     # --------------------------------------------------
#     def _play_audio(self, file_path: str, interrupt_check=lambda: True):
#         pygame.mixer.music.load(file_path)
#         pygame.mixer.music.play()

#         while pygame.mixer.music.get_busy():
#             if not interrupt_check():
#                 break
#             pygame.time.Clock().tick(15)

#         pygame.mixer.music.stop()
#         pygame.mixer.music.unload()  # 🔥 REQUIRED on Windows

#     # --------------------------------------------------
#     # PUBLIC: SPEAK (FAST + FULL CONTENT)
#     # --------------------------------------------------
#     def speak(self, text: str, interrupt_check=lambda: True):
#         """
#         Fast, full-content TTS.
#         - Speaks ALL information
#         - Low perceived latency
#         - Chunked playback
#         """

#         if not text.strip():
#             return

#         # ----------------------------------------------
#         # SPLIT TEXT INTO SPEAKABLE CHUNKS
#         # ----------------------------------------------
#         sentences = [s.strip() for s in text.replace(".", ",").split(",") if s.strip()]
#         chunks = []
#         current_chunk = ""

#         for sentence in sentences:
#             # Keep chunks short for fast TTS generation
#             if len(current_chunk) + len(sentence) < 180:
#                 current_chunk += sentence + ". "
#             else:
#                 chunks.append(current_chunk.strip())
#                 current_chunk = sentence + ". "

#         if current_chunk:
#             chunks.append(current_chunk.strip())

#         # ----------------------------------------------
#         # SPEAK CHUNKS ONE BY ONE
#         # ----------------------------------------------
#         for chunk in chunks:
#             if not interrupt_check():
#                 break

#             audio_file = f"tts_{uuid.uuid4().hex}.mp3"

#             try:
#                 asyncio.run(self._text_to_audio(chunk, audio_file))
#                 self._play_audio(audio_file, interrupt_check)
#             finally:
#                 if os.path.exists(audio_file):
#                     try:
#                         os.remove(audio_file)
#                     except PermissionError:
#                         pass  # Windows may release late

#     # --------------------------------------------------
#     # STOP SPEAKING (OPTIONAL)
#     # --------------------------------------------------
#     def stop(self):
#         pygame.mixer.music.stop()
#         pygame.mixer.quit()


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
