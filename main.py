from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import requests
import subprocess
import os
from dotenv import load_dotenv
import openai

# 🔐 Load secrets from .env
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
WABA_TOKEN = os.getenv("WABA_TOKEN")
MEDIA_DOWNLOAD_DIR = "downloads"
os.makedirs(MEDIA_DOWNLOAD_DIR, exist_ok=True)

app = FastAPI()

# =======================
# 🔧 Helper Functions
# =======================
def get_media_url(media_id):
    url = f"https://graph.facebook.com/v18.0/{media_id}"
    headers = {"Authorization": f"Bearer {WABA_TOKEN}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()["url"]

def download_media_file(media_url, filename="voice_note.ogg"):
    headers = {"Authorization": f"Bearer {WABA_TOKEN}"}
    response = requests.get(media_url, headers=headers)
    response.raise_for_status()
    path = os.path.join(MEDIA_DOWNLOAD_DIR, filename)
    with open(path, "wb") as f:
        f.write(response.content)
    return path

def convert_ogg_to_wav(input_path, output_path):
    command = ["ffmpeg", "-y", "-i", input_path, output_path]
    subprocess.run(command, check=True)
    return output_path

def transcribe_with_whisper(file_path):
    with open(file_path, "rb") as audio_file:
        transcript = openai.audio.translations.create(
            model="whisper-1",
            file=audio_file,
            response_format="text"
        )
    return transcript

# =======================
# 🌐 Webhook Endpoint
# =======================
@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    print("\U0001f4e9 Incoming WhatsApp message:", data)

    try:
        entry = data["entry"][0]
        changes = entry["changes"][0]
        value = changes["value"]
        messages = value.get("messages", [])

        if messages:
            message = messages[0]
            msg_type = message["type"]
            sender = message["from"]

            if msg_type == "text":
                text = message["text"]["body"]
                print(f"💬 Text from {sender}: {text}")

            elif msg_type == "audio":
                media_id = message["audio"]["id"]
                print(f"🎧 Voice from {sender} — Media ID: {media_id}")

                media_url = get_media_url(media_id)
                ogg_path = download_media_file(media_url)
                print("📥 Downloaded OGG:", ogg_path)

                wav_path = os.path.splitext(ogg_path)[0] + ".wav"
                convert_ogg_to_wav(ogg_path, wav_path)
                print("🎵 Converted to WAV:", wav_path)

                transcript = transcribe_with_whisper(wav_path)
                print("📝 Transcription:", transcript)

    except Exception as e:
        print("❌ Webhook error:", e)

    return JSONResponse({"status": "received"})

# print("🔐 OpenAI Key (last 5):", openai.api_key[-5:])
# print("🔐 WABA Token (last 5):", WABA_TOKEN[-5:])
