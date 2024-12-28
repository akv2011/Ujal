import os
import logging
import google.generativeai as genai
import speech_recognition as sr
from dotenv import load_dotenv
from elevenlabs import play
from elevenlabs.client import ElevenLabs
from typing import List, Dict, Optional

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AIAssistant:
    """
    An AI assistant that combines speech recognition, text generation, and text-to-speech capabilities.
    
    Attributes:
        elevenlabs_api_key (str): API key for ElevenLabs text-to-speech service
        gemini_api_key (str): API key for Google's Gemini AI model
        full_transcript (List[Dict]): History of conversation between user and AI
    """
    
    def __init__(self):
        # Load environment variables
        load_dotenv(verbose=True)
        
        # Initialize API keys with proper validation
        self.elevenlabs_api_key = self._validate_api_key("ELEVENLABS_API_KEY")
        self.gemini_api_key = self._validate_api_key("GEMINI_API_KEY")
        
        # Initialize conversation history
        self.full_transcript: List[Dict[str, str]] = []
        
        # Initialize ElevenLabs client
        self.eleven_client = ElevenLabs(api_key=self.elevenlabs_api_key)
        
        # Configure Gemini
        genai.configure(api_key=self.gemini_api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")
        
        # Initialize speech recognizer
        self.recognizer = sr.Recognizer()
        
        logger.info("AI Assistant initialized successfully")

    def _validate_api_key(self, key_name: str) -> str:
        """Validate the presence and format of API keys."""
        api_key = os.getenv(key_name)
        if not api_key:
            raise ValueError(f"{key_name} not found in environment variables")
        if len(api_key) < 32:  # Basic validation for API key format
            raise ValueError(f"{key_name} appears to be invalid")
        return api_key

    def list_available_voices(self) -> List[Dict[str, str]]:
        """
        Retrieve and display available voices from ElevenLabs.
        Returns a list of voice information dictionaries.
        """
        try:
            voices = self.eleven_client.voices.get_all()
            logger.info("Successfully retrieved voices from ElevenLabs")
            
            voice_list = []
            print("\nAvailable voices:")
            for voice in voices:
                # Handle different response formats safely
                voice_info = {
                    'name': getattr(voice, 'name', str(voice)),
                    'id': getattr(voice, 'voice_id', None)
                }
                print(f"- {voice_info['name']} (ID: {voice_info['id']})")
                voice_list.append(voice_info)
            return voice_list
            
        except Exception as e:
            logger.error(f"Error retrieving voices: {str(e)}")
            return []

    def speech_to_text(self) -> Optional[str]:
        """
        Convert spoken audio to text using speech recognition.
        Returns the recognized text or None if recognition fails.
        """
        try:
            with sr.Microphone() as source:
                print("\nListening...")
                # Adjust for ambient noise before listening
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=10, phrase_time_limit=15)

            text = self.recognizer.recognize_google(audio)
            logger.info(f"Successfully recognized speech: {text}")
            return text
            
        except sr.WaitTimeoutError:
            logger.warning("No speech detected within timeout period")
            print("No speech detected. Please try again.")
        except sr.UnknownValueError:
            logger.warning("Speech was not understood")
            print("Sorry, I couldn't understand that. Please try again.")
        except sr.RequestError as e:
            logger.error(f"Speech recognition service error: {str(e)}")
            print("There was an error with the speech recognition service.")
        except Exception as e:
            logger.error(f"Unexpected error in speech recognition: {str(e)}")
            print("An unexpected error occurred. Please try again.")
        
        return None

    def generate_ai_response(self, text: str) -> Optional[str]:
        """
        Generate AI response using the Gemini model.
        Args:
            text: User's input text
        Returns:
            Generated response text or None if generation fails
        """
        try:
            self.full_transcript.append({"role": "user", "content": text})
            
            response = self.model.generate_content(
                "You are a helpful AI assistant. Respond to: " + text,
                safety_settings=[
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                ]
            )
            
            response_text = response.text
            self.full_transcript.append({"role": "assistant", "content": response_text})
            logger.info("Successfully generated AI response")
            return response_text
            
        except Exception as e:
            logger.error(f"Error generating AI response: {str(e)}")
            return None

    def generate_audio(self, text: str) -> bool:
        """
        Generate and play audio from text using ElevenLabs.
        Args:
            text: Text to convert to speech
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            audio = self.eleven_client.generate(
                text=text,
                voice="Josh",  # Using a default voice
                model="eleven_multilingual_v2",
                stability=0.5,
                similarity_boost=0.75
            )
            
            # Save audio to file instead of direct playback
            with open("response.mp3", "wb") as f:
                f.write(audio)
            
            # Use a different audio player if ALSA is not working
            os.system("mpg123 response.mp3")  # Requires mpg123 to be installed
            logger.info("Successfully generated and played audio")
            return True
            
        except Exception as e:
            logger.error(f"Error generating audio: {str(e)}")
            return False

    def run(self):
        """Main loop for the AI assistant."""
        print("\nAI Assistant initialized. Ready to help!")
        
        while True:
            try:
                # Get speech input
                text = self.speech_to_text()
                if not text:
                    continue
                
                # Generate and display AI response
                response = self.generate_ai_response(text)
                if response:
                    print(f"\nAI: {response}")
                    
                    # Generate audio response
                    if not self.generate_audio(response):
                        print("Note: Audio response failed, but text response is available.")
                
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                logger.error(f"Unexpected error in main loop: {str(e)}")
                print("An error occurred. Continuing...")

if __name__ == "__main__":
    try:
        assistant = AIAssistant()
        assistant.run()
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        print("Failed to initialize AI Assistant. Please check your configuration.")