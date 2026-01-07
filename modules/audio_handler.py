"""
Audio Handler Module
Handles Speech-to-Text (Whisper) and Text-to-Speech (OpenAI TTS)
"""
import os
import logging
from pathlib import Path
from typing import Optional
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def transcribe_audio(audio_file_path: str) -> Optional[str]:
    """
    Transcribe audio to text using OpenAI Whisper API.
    
    Args:
        audio_file_path: Path to the audio file
        
    Returns:
        Transcribed text, or None if transcription fails
    """
    try:
        # Check if file exists
        if not os.path.exists(audio_file_path):
            logger.error(f"Audio file not found at {audio_file_path}")
            return None
        
        # Open and transcribe the audio file
        with open(audio_file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text"
            )
        
        return transcript.strip() if transcript else None
        
    except Exception as e:
        logger.error(f"Error transcribing audio: {str(e)}")
        return None


def text_to_speech(text: str, output_path: Optional[str] = None) -> Optional[str]:
    """
    Convert text to speech using OpenAI TTS API.
    
    Args:
        text: Text to convert to speech
        output_path: Optional path to save the audio file. If None, uses temp directory.
        
    Returns:
        Path to the generated audio file, or None if generation fails
    """
    try:
        # Generate a default output path if not provided
        if output_path is None:
            # Create a temp directory if it doesn't exist (Windows compatible)
            import tempfile
            import hashlib
            temp_base = Path(tempfile.gettempdir())
            temp_dir = temp_base / "autonomous_recruiter_audio"
            temp_dir.mkdir(parents=True, exist_ok=True)
            # Use MD5 hash for consistent, collision-resistant filenames
            text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
            output_path = str(temp_dir / f"tts_{text_hash}.mp3")
        
        # Generate speech
        response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",  # Professional, neutral voice
            input=text
        )
        
        # Save to file
        response.stream_to_file(output_path)
        
        return output_path
        
    except Exception as e:
        logger.error(f"Error generating speech: {str(e)}")
        return None


def transcribe_chainlit_audio(audio_element) -> Optional[str]:
    """
    Transcribe audio from a Chainlit audio element.
    
    Args:
        audio_element: Chainlit audio element from message
        
    Returns:
        Transcribed text, or None if transcription fails
    """
    try:
        if hasattr(audio_element, 'path'):
            return transcribe_audio(audio_element.path)
        return None
    except Exception as e:
        logger.error(f"Error transcribing Chainlit audio: {str(e)}")
        return None
