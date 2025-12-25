import json
import os
from datetime import datetime

HISTORY_FILE = "conversation_history.json"
MAX_HISTORY = 10  # last N exchanges sent to AI


class ConversationMemory:
    def __init__(self, file_path=HISTORY_FILE):
        self.file_path = file_path
        self.history = []
        self._load()

    def _load(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    self.history = json.load(f)
            except Exception:
                self.history = []

    def _save(self):
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self.history, f, indent=2)

    def add(self, role: str, content: str):
        entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "role": role,
            "content": content,
        }
        self.history.append(entry)
        self._save()

    def get_recent_for_llm(self):
        """
        Returns last N messages formatted for Groq/OpenAI
        """
        recent = self.history[-MAX_HISTORY:]
        return [{"role": h["role"], "content": h["content"]} for h in recent]

    def clear(self):
        self.history = []
        self._save()
