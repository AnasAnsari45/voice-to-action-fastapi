from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import requests
import subprocess
import os
import json  # Required for parsing Hugging Face response
from dotenv import load_dotenv
import openai

# 🔐 Load secrets from .env file
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
WABA_TOKEN = os.getenv("WABA_TOKEN")
HF_API_TOKEN = os.getenv("HF_API_TOKEN")
# HF_MODEL_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct"

HF_MODEL_URL = "https://api-inference.huggingface.co/models/HuggingFaceH4/zephyr-7b-beta"

# 📁 Media download directory
MEDIA_DOWNLOAD_DIR = "downloads"
os.makedirs(MEDIA_DOWNLOAD_DIR, exist_ok=True)

app = FastAPI()

# ========================
# 🔧 Utility Functions
# ========================

def get_media_url(media_id):
    """Fetch media download URL from WhatsApp API using media_id"""
    url = f"https://graph.facebook.com/v18.0/{media_id}"
    headers = {"Authorization": f"Bearer {WABA_TOKEN}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()["url"]

def download_media_file(media_url, filename="voice_note.ogg"):
    """Download audio file from WhatsApp to local storage"""
    headers = {"Authorization": f"Bearer {WABA_TOKEN}"}
    response = requests.get(media_url, headers=headers)
    response.raise_for_status()
    path = os.path.join(MEDIA_DOWNLOAD_DIR, filename)
    with open(path, "wb") as f:
        f.write(response.content)
    return path

def convert_ogg_to_wav(input_path, output_path):
    """Convert OGG audio to WAV using ffmpeg"""
    command = ["ffmpeg", "-y", "-i", input_path, output_path]
    subprocess.run(command, check=True)
    return output_path

def transcribe_with_whisper(file_path):
    """Use OpenAI Whisper to transcribe multilingual audio"""
    try:
        with open(file_path, "rb") as audio_file:
            transcript = openai.audio.translations.create(
                model="whisper-1",
                file=audio_file,
                response_format="text"
            )
        print("📝 Transcription successful:", transcript)
        return transcript
    except Exception as e:
        print("❌ Whisper API failed:", e)
        return None

# def structure_transcription(text):
#     """Call Hugging Face model to structure text into JSON"""
#     prompt = f"""
#     Extract structured information from this report and return as JSON:
#     ---
#     Report: "{text}"
#     ---
#     Format:
#     {{
#       "agent_name": "",
#       "store_or_location": "",
#       "product_issues": [],
#       "equipment_issues": [],
#       "complaints_or_requests": [],
#       "misc": []
#     }}
#     """
#     headers = {
#         "Authorization": f"Bearer {HF_API_TOKEN}",
#         "Content-Type": "application/json"
#     }

#     response = requests.post(HF_MODEL_URL, headers=headers, json={"inputs": prompt})
#     if response.status_code == 200:
#         output = response.json()
#         try:
#             return json.loads(output[0]["generated_text"].split("```")[0])  # removes Markdown backticks
#         except Exception as e:
#             print("⚠️ Failed to parse structured response:", e)
#             return output[0]["generated_text"]
#     else:
#         print("❌ Hugging Face API error:", response.text)
#         return {"error": response.text}

import re
import json

def structure_transcription(text):
    prompt = f"""
Extract structured information from this report and return as JSON.

Example:
Report: "My name is Sarah. I am at AlFatah Store. They are out of detergent and their cash register is broken."
JSON:
{{
  "agent_name": "Sarah",
  "store_or_location": "AlFatah Store",
  "product_issues": ["out of detergent"],
  "equipment_issues": ["cash register is broken"],
  "complaints_or_requests": [],
  "misc": []
}}

Now extract for:
Report: "{text}"
JSON:
"""

    headers = {
        "Authorization": f"Bearer {HF_API_TOKEN}",
        "Content-Type": "application/json"
    }

    response = requests.post(HF_MODEL_URL, headers=headers, json={"inputs": prompt})
    
    if response.status_code == 200:
        output = response.json()
        try:
            # ✅ Extract JSON block using regex (anything between { and })
            match = re.search(r"\{[\s\S]*?\}", output[0]["generated_text"])
            if match:
                structured = json.loads(match.group())
                print("📦 Structured Output (parsed JSON):", structured)
                return structured
            else:
                print("⚠️ No JSON found in model response.")
                return output[0]["generated_text"]
        except Exception as e:
            print("⚠️ Failed to parse structured response:", e)
            print("📦 Structured Output (raw):", output[0]["generated_text"])
            return output[0]["generated_text"]
    else:
        print("❌ Hugging Face API error:", response.text)
        return {"error": response.text}

# import json

# HF_MODEL_URL = "https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct"

# def structure_transcription(text):
#     prompt = f"""
# Extract structured information from this report and return as JSON.

# Example:
# Report: "My name is Sarah. I am at AlFatah Store. They are out of detergent and their cash register is broken."
# JSON:
# {{
#   "agent_name": "Sarah",
#   "store_or_location": "AlFatah Store",
#   "product_issues": ["out of detergent"],
#   "equipment_issues": ["cash register is broken"],
#   "complaints_or_requests": [],
#   "misc": []
# }}

# Now extract for:
# Report: "{text}"
# JSON:
# """

#     headers = {
#         "Authorization": f"Bearer {HF_API_TOKEN}",
#         "Content-Type": "application/json"
#     }

#     response = requests.post(HF_MODEL_URL, headers=headers, json={"inputs": prompt})

#     if response.status_code == 200:
#         output = response.json()
#         try:
#             raw_text = output[0]["generated_text"]
#             json_start = raw_text.find("{")
#             json_data = raw_text[json_start:]
#             structured_output = json.loads(json_data)
#             print("📦 Structured Output (parsed JSON):", structured_output)
#             return structured_output
#         except Exception as e:
#             print("⚠️ Failed to parse structured response:", e)
#             print("📦 Structured Output:", raw_text)
#             return raw_text
#     else:
#         print("❌ Hugging Face API error:", response.text)
#         return {"error": response.text}



# ========================
# 🌐 WhatsApp Webhook
# ========================

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    print("📩 Incoming WhatsApp message:", data)

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

                # 🔽 Download & Convert
                media_url = get_media_url(media_id)
                ogg_path = download_media_file(media_url)
                print("📥 Downloaded OGG:", ogg_path)

                wav_path = os.path.splitext(ogg_path)[0] + ".wav"
                convert_ogg_to_wav(ogg_path, wav_path)
                print("🎵 Converted to WAV:", wav_path)

                # 🧠 Transcribe
                print("🧠 Starting transcription...")
                transcription = transcribe_with_whisper(wav_path)
                print("🧠 Transcription output:", transcription)

                # 🧩 Structure into JSON
                if transcription:
                    structured_data = structure_transcription(transcription)
                    print("📦 Structured Output:", structured_data)
                else:
                    print("⚠️ Skipping structuring due to failed transcription")

    except Exception as e:
        print("❌ Webhook error:", e)

    return JSONResponse({"status": "received"})
