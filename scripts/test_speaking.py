"""Test speaking endpoint with multipart upload."""
import sys
from pathlib import Path

import httpx

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)

BASE_URL = "http://127.0.0.1:8000"
BOOK_ID = "7adbf117-707a-4ae6-8b74-735179db49c4"
AUDIO_FILE = Path(r"C:\Projects\ai-english-tutor\scripts\fixtures\AEF3e_Level_2_SB_1.11.mp3")


def main() -> int:
    print("STEP 1: Checking if file exists...")
    if not AUDIO_FILE.exists():
        print(f"ERROR: Audio file not found: {AUDIO_FILE}")
        return 1
    print(f"OK. File size: {AUDIO_FILE.stat().st_size // 1024} KB")

    print("\nSTEP 2: Creating tutor session...")
    try:
        sess_resp = httpx.post(
            f"{BASE_URL}/api/v1/tutor/sessions",
            json={"book_id": BOOK_ID, "mode": "free"},
            timeout=10.0,
        )
        sess_resp.raise_for_status()
    except Exception as e:
        print(f"ERROR creating session: {e}")
        return 1
    session_id = sess_resp.json()["id"]
    print(f"OK. Session: {session_id}")

    print(f"\nSTEP 3: Uploading audio...")
    print("(This will take 30-60 seconds: STT + LLM + TTS)")
    try:
        with AUDIO_FILE.open("rb") as f:
            files = {"audio": (AUDIO_FILE.name, f, "audio/mpeg")}
            data = {"session_id": session_id}
            resp = httpx.post(
                f"{BASE_URL}/api/v1/speaking/attempts",
                data=data,
                files=files,
                timeout=180.0,
            )
        resp.raise_for_status()
    except Exception as e:
        print(f"ERROR uploading audio: {e}")
        if hasattr(e, "response") and e.response is not None:
            print(f"Response status: {e.response.status_code}")
            print(f"Response body: {e.response.text[:1000]}")
        return 1

    result = resp.json()
    print("\n=== RESULT ===")
    print(f"Attempt ID: {result['id']}")
    print(f"Pronunciation: {result['pronunciation_status']}")
    print(f"\nTranscript ({len(result['transcript'])} chars):")
    print(result["transcript"][:500])
    print(f"\nFeedback:")
    print(result["feedback_text"])
    print(f"\nAudio reply URL: {BASE_URL}{result['reply_audio_url']}")
    return 0


if __name__ == "__main__":
    print("=== Speaking Test Script Starting ===")
    exit_code = main()
    print(f"=== Script finished with exit code {exit_code} ===")
    sys.exit(exit_code)