import base64
import logging
import sqlite3
import os
import numpy as np
import re
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from typing import List

from exceptions import ExceptionCustom

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app initialization
app = FastAPI()

# SQLite Database Configuration
DATABASE = os.getenv("DATABASE", "audio_metadata.db")


def init_db():
    """
    Initializes the SQLite database and creates the audio_metadata table if it doesn't exist.
    """
    with sqlite3.connect(DATABASE) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS audio_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                file_name TEXT NOT NULL,
                length_seconds REAL NOT NULL
            )
        """)
        conn.commit()
    logger.info("Database initialized successfully.")


init_db()


# Pydantic models
class AudioFile(BaseModel):
    file_name: str
    encoded_audio: str


class AudioPayload(BaseModel):
    session_id: str
    timestamp: str
    audio_files: List[AudioFile]


def calculate_audio_length(audio_array: np.ndarray, sample_rate: int) -> float:
    """
    Calculates the duration of an audio file in seconds.

    Args:
        audio_array (np.ndarray): The audio data as a NumPy array.
        sample_rate (int): The sample rate of the audio.

    Returns:
        float: The duration of the audio in seconds.
    """
    return len(audio_array) / sample_rate


def store_audio_metadata(session_id: str, timestamp: str, file_name: str, length_seconds: float):
    """
    Stores audio metadata in the SQLite database.

    Args:
        session_id (str): The session ID.
        timestamp (str): The timestamp of the audio file.
        file_name (str): The name of the audio file.
        length_seconds (float): The length of the audio file in seconds.

    Raises:
        HTTPException: If there is an error during database insertion.
    """
    try:
        with sqlite3.connect(DATABASE) as conn:
            conn.execute("""
                INSERT INTO audio_metadata (session_id, timestamp, file_name, length_seconds)
                VALUES (?, ?, ?, ?)
            """, (session_id, timestamp, file_name, length_seconds))
            conn.commit()
        logger.info(f"Metadata stored successfully for file: {file_name}")
    except Exception as e:
        logger.error(f"Error storing metadata for {file_name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to store audio metadata")


def validate_audio_files_present(audio_files: list[AudioFile]):
    if not audio_files:
        raise ExceptionCustom(status_code=400, detail="No audio files provided!")
    return True


def validate_timestamp(timestamp: str):
    timestamp_pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$"
    if not re.fullmatch(timestamp_pattern, timestamp):
        raise ExceptionCustom(status_code=400, detail="Invalid timestamp format!")
    return True


def validate_audio_file(audio_files: list[AudioFile]):
    for audio_file in audio_files:
        try:
            decoded = base64.b64decode(audio_file.encoded_audio, validate=True)
            if base64.b64encode(decoded).decode() == audio_file.encoded_audio:
                return True
        except Exception as e:
            logger.warning(f"Base64 validation error for file {audio_file.file_name}: {e}")
            raise ExceptionCustom(status_code=400, detail="Invalid base64 encoding file!")


def validate_payload(payload: AudioPayload) -> bool:
    """
    Validates the audio payload structure and contents.

    Args:
        payload (AudioPayload): The payload containing audio metadata and files.

    Returns:
        bool: True if the payload is valid, False otherwise.
    """
    if (validate_audio_files_present(payload.audio_files) and
            validate_timestamp(payload.timestamp) and
            validate_audio_file(payload.audio_files)):
        return True
    else:
        return False


@app.post("/process-audio")
async def process_audio(payload: AudioPayload):
    """
    Processes uploaded audio files and stores their metadata in the database.

    Args:
        payload (AudioPayload): The payload containing session details and audio files.

    Returns:
        dict: A response indicating success or failure of processing.
    """
    sample_rate = 4000
    processed_files = []

    if not validate_payload(payload):
        return {
            "status": "error",
            "message": "Invalid audio file metadata or payload."
        }

    for audio_file in payload.audio_files:
        try:
            audio_array = np.frombuffer(base64.b64decode(audio_file.encoded_audio), dtype=np.int16)
            length_seconds = calculate_audio_length(audio_array, sample_rate)

            store_audio_metadata(payload.session_id, payload.timestamp, audio_file.file_name, length_seconds)

            processed_files.append({
                "file_name": audio_file.file_name,
                "length_seconds": round(length_seconds, 2)
            })
        except HTTPException as e:
            logger.error(f"Failed to process file {audio_file.file_name}: {e.detail}")
            continue
        except Exception as e:
            logger.error(f"Unexpected error processing file {audio_file.file_name}: {e}")
            continue

    return {
        "status": "success",
        "processed_files": processed_files
    }
