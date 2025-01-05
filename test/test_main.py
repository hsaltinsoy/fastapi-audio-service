import base64
import os

import numpy as np
import pytest
import sqlite3
from fastapi.testclient import TestClient
from main import app, init_db, AudioFile, AudioPayload


# Test Setup
@pytest.fixture(autouse=True)
def setup_and_teardown():
    # Initialize database before each test
    init_db()
    yield
    conn = sqlite3.connect(os.getenv("DATABASE", "audio_metadata.db"))
    cursor = conn.cursor()
    cursor.execute("DELETE FROM audio_metadata")
    conn.commit()
    conn.close()


# Function to create a base64 encoded audio file
def encode_audio() -> bytes:
    return base64.b64encode(np.random.randint(-32768, 32767, 4000, dtype=np.int16).tobytes())


# Function to create a non base64 encoded audio file
def encode_invalid_audio() -> str:
    return str(np.random.randint(-32768, 32767, 4000, dtype=np.int16))


# Test Case 1: Process Audio and Store Metadata
def test_process_audio():
    encoded_audio = encode_audio()

    payload = AudioPayload(
        session_id="test-session",
        timestamp="2025-01-02T12:00:00Z",
        audio_files=[AudioFile(file_name="test_audio.wav", encoded_audio=encoded_audio)],
    )

    client = TestClient(app)
    response = client.post("/process-audio", json=payload.dict())

    assert response.status_code == 200

    response_json = response.json()
    assert response_json["status"] == "success"
    assert "processed_files" in response_json

    conn = sqlite3.connect(os.getenv("DATABASE", "audio_metadata.db"))
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM audio_metadata")
    rows = cursor.fetchall()
    conn.close()

    assert len(rows) > 0

    db_metadata = rows[0]
    assert db_metadata[1] == "test-session"
    assert db_metadata[2] == "2025-01-02T12:00:00Z"
    assert db_metadata[3] == "test_audio.wav"
    assert isinstance(db_metadata[4], float)


# Test Case 2: Empty Audio Files List
def test_empty_audio_files():
    payload = AudioPayload(
        session_id="test-session",
        timestamp="2025-01-02T12:00:00Z",
        audio_files=[],
    )

    client = TestClient(app)
    response = client.post("/process-audio", json=payload.dict())

    assert response.status_code == 400
    assert response.json()["detail"] == "No audio files provided!"


# Test Case 3: Invalid Base64 Encoding
def test_invalid_base64_audio():
    encoded_audio = encode_invalid_audio()
    payload = AudioPayload(
        session_id="test-session",
        timestamp="2025-01-02T12:00:00Z",
        audio_files=[AudioFile(file_name="test_audio.wav", encoded_audio=encoded_audio)],
    )

    client = TestClient(app)
    response = client.post("/process-audio", json=payload.dict())

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid base64 encoding file!"


# Test Case 4: Invalid Timestamp Format
def test_invalid_timestamp_format():
    encoded_audio = encode_audio()

    payload = AudioPayload(
        session_id="test-session",
        timestamp="2025-01-02T12:00:00",  # Invalid timestamp format
        audio_files=[AudioFile(file_name="test_audio.wav", encoded_audio=encoded_audio)],
    )

    client = TestClient(app)
    response = client.post("/process-audio", json=payload.dict())

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid timestamp format!"


# Test Case 5: Process Multiple Audio Files
def test_process_multiple_audio_files():
    encoded_audio_1 = encode_audio()
    encoded_audio_2 = encode_audio()

    payload = AudioPayload(
        session_id="test-session",
        timestamp="2025-01-02T12:00:00Z",
        audio_files=[
            AudioFile(file_name="test_audio_1.wav", encoded_audio=encoded_audio_1),
            AudioFile(file_name="test_audio_2.wav", encoded_audio=encoded_audio_2),
        ],
    )

    client = TestClient(app)
    response = client.post("/process-audio", json=payload.dict())

    assert response.status_code == 200

    response_json = response.json()
    assert len(response_json["processed_files"]) == 2  # Two files should be processed

    conn = sqlite3.connect(os.getenv("DATABASE", "audio_metadata.db"))
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM audio_metadata")
    rows = cursor.fetchall()
    conn.close()

    assert len(rows) == 2  # Two rows should be inserted for the two audio files
