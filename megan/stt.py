import speech_recognition as sr
import time

class SpeechToText:
    def __init__(self):
        self.recognizer = sr.Recognizer()

        # 🔥 Tuned for conversational assistants
        self.recognizer.pause_threshold = 0.6
        self.recognizer.energy_threshold = 250
        self.recognizer.dynamic_energy_threshold = True

        self.microphone = sr.Microphone()

        # Calibrate ONCE at startup
        with self.microphone as source:
            print("Calibrating microphone...")
            self.recognizer.adjust_for_ambient_noise(source, duration=1.0)
            print("Calibration done")

    def listen(self) -> str:
        print("Listening...")

        try:
            with self.microphone as source:
                audio = self.recognizer.listen(
                    source,
                    timeout=4,             # wait max 4 sec for speech
                    phrase_time_limit=8    # max length of one sentence
                )

            text = self.recognizer.recognize_google(audio)
            print("Heard:", text)
            return text.strip()

        except sr.WaitTimeoutError:
            # No speech detected quickly enough
            return ""

        except sr.UnknownValueError:
            print("Could not understand audio")
            return ""

        except sr.RequestError as e:
            print("Speech API error:", e)
            return ""
