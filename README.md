# Audio Metadata Processor API

The **Audio Metadata Processor API** is a FastAPI-based application for processing audio files. It extracts key metadata such as the audio length (in seconds) and stores this information in an SQLite database. The API accepts audio files encoded in Base64 and provides detailed metadata for each processed file.

---

## Features

### Core Functionality
- **Multi-file Support**: Accepts multiple audio files in a single POST request.
- **Base64 Decoding**: Decodes Base64-encoded audio files.
- **Metadata Extraction**: Calculates and records the length of each audio file in seconds.
- **Data Storage**: Stores metadata, including session ID, timestamp, file name, and audio length, in an SQLite database.

### Request Validation
- Validates request data using **Pydantic models** for robust input validation.

### Error Handling
- Comprehensive error handling for:
  - Invalid Base64 encoding.
  - Missing or empty audio files.
  - Unsupported file formats or other common issues.

---

## Installation Guide

Follow these steps to install and run the application:

### 1. Clone the Repository
```bash
git clone https://github.com/hsaltinsoy/fastapi-audio-service.git
cd fastapi-audio-service
```

### 2. Install Dependencies
Ensure you have Python installed. Then, install the required Python packages:
```bash
pip install -r requirements.txt
```

### 3. Run the Application
Navigate to the `src` directory and start the FastAPI application using Uvicorn:
```bash
cd src
uvicorn main:app --reload
```

---

## Usage

### API Endpoints

#### 1. **Upload and Process Audio Files**
- **Endpoint**: `POST /upload`
- **Description**: Accepts one or more Base64-encoded audio files and processes them.
- **Request Payload**:
  ```json
  {
    "session_id": "unique-session-id",
    "files": [
      {
        "file_name": "example.mp3",
        "data": "<Base64-encoded audio string>"
      },
      {
        "file_name": "example2.wav",
        "data": "<Base64-encoded audio string>"
      }
    ]
  }
  ```
- **Response**:
  ```json
  {
    "status": "success",
    "metadata": [
      {
        "file_name": "example.mp3",
        "length_seconds": 120,
        "timestamp": "2025-01-01T10:00:00Z"
      },
      {
        "file_name": "example2.wav",
        "length_seconds": 300,
        "timestamp": "2025-01-01T10:00:05Z"
      }
    ]
  }
  ```
- **Error Responses**:
  - **Invalid Base64 Encoding** (400 Bad Request):
    ```json
    {
      "status_code": 400,
      "detail": "Invalid Base64 encoding."
    }
    ```
  - **Empty File** (400 Bad Request):
    ```json
    {
      "status_code": 400,
      "detail": "Uploaded file is empty."
    }
    ```

---

### Metadata Stored in the Database

Each processed file's metadata is stored in an SQLite database with the following fields:

- **Session ID**: Unique identifier for the upload session.
- **Timestamp**: Time when the file was processed.
- **File Name**: Name of the uploaded audio file.
- **Audio Length (seconds)**: Duration of the audio in seconds.
