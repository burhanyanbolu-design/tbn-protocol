"""
Human AI — Speech Module (Free, Natural Voice)
===============================================
Text-to-Speech: edge-tts (Microsoft neural voices — free, sounds human)
Speech-to-Text: vosk (offline model)

No API keys. Free. Natural sounding.
"""

import os
import sys
import json
import asyncio
import tempfile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ============================================================================
# TEXT-TO-SPEECH (edge-tts — free, natural neural voices)
# ============================================================================

class TextToSpeechEngine:
    """Natural text-to-speech using Microsoft Edge neural voices (free)"""

    # Good natural-sounding voices
    VOICES = {
        "female_uk": "en-GB-SoniaNeural",
        "male_uk": "en-GB-RyanNeural",
        "female_us": "en-US-JennyNeural",
        "male_us": "en-US-GuyNeural",
        "female_au": "en-AU-NatashaNeural",
    }

    def __init__(self, voice: str = "en-GB-SoniaNeural", rate: str = "+0%"):
        self.voice = voice
        self.rate = rate
        self._temp_dir = os.path.join(BASE_DIR, ".audio_cache")
        os.makedirs(self._temp_dir, exist_ok=True)

    def speak(self, text: str):
        """Speak text aloud using neural voice"""
        print(f"  [Speaking]: {text[:80]}...")
        asyncio.run(self._speak_async(text))

    async def _speak_async(self, text: str):
        """Generate speech and play it"""
        import edge_tts

        # Generate audio file
        audio_path = os.path.join(self._temp_dir, "speech.mp3")
        communicate = edge_tts.Communicate(text, self.voice, rate=self.rate)
        await communicate.save(audio_path)

        # Play with pygame
        self._play_audio(audio_path)

    def _play_audio(self, path: str):
        """Play audio file"""
        try:
            import pygame
            pygame.mixer.init()
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.wait(100)
            pygame.mixer.quit()
        except Exception as e:
            # Fallback: use system player
            os.system(f'start /min "" "{path}"')
            import time
            time.sleep(2)

    def set_rate(self, rate: int):
        """Set rate as percentage offset. e.g. -20 for slower, +20 for faster"""
        if rate >= 0:
            self.rate = f"+{rate}%"
        else:
            self.rate = f"{rate}%"

    def set_volume(self, volume: float):
        """Volume not directly supported in edge-tts, handled by pygame"""
        pass

    def set_voice(self, voice_name: str):
        """Set voice by name"""
        self.voice = voice_name

    def list_voices(self):
        """List available natural voices"""
        print("  Available Neural Voices (free):")
        print("  ─────────────────────────────────────")
        for key, voice in self.VOICES.items():
            marker = " ← current" if voice == self.voice else ""
            print(f"  [{key}] {voice}{marker}")
        print("\n  Set with: voice-settings")
        return self.VOICES


# ============================================================================
# SPEECH-TO-TEXT (vosk — free, offline)
# ============================================================================

class SpeechRecognitionEngine:
    """Offline speech recognition using vosk"""

    MODEL_PATH = os.path.join(BASE_DIR, "vosk-model")

    def __init__(self):
        self.model = None
        self.recognizer = None
        self._check_model()

    def _check_model(self):
        """Check if vosk model is downloaded"""
        if not os.path.exists(self.MODEL_PATH):
            print("\n  Vosk model not found.")
            print(f"  Download a small English model from:")
            print(f"  https://alphacephei.com/vosk/models")
            print(f"  Extract to: {self.MODEL_PATH}")
            print(f"  Recommended: vosk-model-small-en-us-0.15 (40MB)\n")
            return False
        return True

    def _init_model(self):
        """Initialize vosk model"""
        if self.model is None:
            from vosk import Model, KaldiRecognizer
            print("  Loading speech model...")
            self.model = Model(self.MODEL_PATH)
            print("  Model loaded.")
        return True

    def listen(self, timeout: int = 5) -> str:
        """Listen for speech and return text"""
        try:
            import pyaudio
            from vosk import Model, KaldiRecognizer

            if not self._init_model():
                return ""

            rec = KaldiRecognizer(self.model, 16000)

            p = pyaudio.PyAudio()
            stream = p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=4000
            )

            print("  🎤 Listening... (speak now)")

            result_text = ""
            silence_count = 0
            max_silence = timeout * 4  # ~4 chunks per second

            while silence_count < max_silence:
                data = stream.read(4000, exception_on_overflow=False)
                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    if result.get("text"):
                        result_text = result["text"]
                        break
                else:
                    partial = json.loads(rec.PartialResult())
                    if not partial.get("partial"):
                        silence_count += 1
                    else:
                        silence_count = 0

            # Get final result
            if not result_text:
                final = json.loads(rec.FinalResult())
                result_text = final.get("text", "")

            stream.stop_stream()
            stream.close()
            p.terminate()

            return result_text.strip()

        except ImportError as e:
            print(f"  Missing dependency: {e}")
            print("  Install: pip install pyaudio vosk")
            return ""
        except Exception as e:
            print(f"  Microphone error: {e}")
            return ""


# ============================================================================
# VOICE ASSISTANT (Combines TTS + STT + Human AI)
# ============================================================================

class VoiceAssistant:
    """Interactive voice conversation with Human AI"""

    def __init__(self, ai_system):
        self.ai = ai_system
        self.tts = TextToSpeechEngine(voice="en-GB-SoniaNeural")
        self.stt = SpeechRecognitionEngine()
        self.active = False

    def start_conversation(self):
        """Start voice conversation loop"""
        print("\n" + "=" * 50)
        print("  HUMAN AI — Voice Mode")
        print("=" * 50)
        print("  Say something, or say 'exit' to stop.")
        print("  Press Ctrl+C to force quit.\n")

        self.tts.speak("Hello. I'm Human AI. How can I help you?")
        self.active = True

        while self.active:
            try:
                # Listen
                user_text = self.stt.listen(timeout=8)

                if not user_text:
                    print("  (no speech detected, listening again...)")
                    continue

                print(f"  You: {user_text}")

                # Check for exit
                if user_text.lower() in ("exit", "quit", "stop", "goodbye", "bye"):
                    self.tts.speak("Goodbye. Take care.")
                    self.active = False
                    break

                # Process through Human AI
                result = self.ai.process(user_text)
                response = result.get("response", "I'm not sure how to respond to that.")

                print(f"  AI: {response}")
                self.tts.speak(response)

            except KeyboardInterrupt:
                print("\n  Voice mode ended.")
                self.active = False
                break
            except Exception as e:
                print(f"  Error: {e}")
                continue

        print("\n  Returned to text mode.\n")


# ============================================================================
# STANDALONE TEST
# ============================================================================

if __name__ == "__main__":
    print("\n  Testing Speech Module...\n")

    # Test TTS
    print("  1. Testing Text-to-Speech (neural voice)...")
    tts = TextToSpeechEngine()
    tts.list_voices()
    tts.speak("Hello. I am Human AI. I sound natural because I use neural voices, completely free.")

    # Test STT
    print("\n  2. Testing Speech Recognition...")
    stt = SpeechRecognitionEngine()
    if stt._check_model():
        text = stt.listen(timeout=5)
        print(f"  You said: '{text}'")
    else:
        print("  (Skipped — download vosk model first)")

    print("\n  Done.")
