# from fastapi import FastAPI, Request
# from fastapi.responses import PlainTextResponse, JSONResponse

# app = FastAPI()

 VERIFY_TOKEN = "voiceaction123"  # Match this in Meta webhook form

# @app.get("/webhook")
# async def verify(request: Request):
#     params = dict(request.query_params)
#     if params.get("hub.mode") == "subscribe" and params.get("hub.verify_token") == VERIFY_TOKEN:
#         return PlainTextResponse(content=params["hub.challenge"])
#     return PlainTextResponse("Verification failed", status_code=403)

# @app.post("/webhook")
# async def webhook(request: Request):
#     data = await request.json()
#     print("📩 Incoming WhatsApp message:", data)
#     return JSONResponse({"status": "received"})



from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

# @app.post("/webhook")
# async def webhook(request: Request):
#     data = await request.json()
#     print("📩 Full incoming payload:", data)

#     try:
#         # Step 1: Access message
#         entry = data["entry"][0]
#         change = entry["changes"][0]
#         value = change["value"]
#         messages = value.get("messages", [])

#         if messages:
#             message = messages[0]
#             msg_type = message["type"]
#             sender = message["from"]

#             print(f"📨 New message from {sender}, type: {msg_type}")

#             if msg_type == "audio":
#                 media_id = message["audio"]["id"]
#                 print(f"🎧 Voice note received — Media ID: {media_id}")

#             elif msg_type == "text":
#                 text = message["text"]["body"]
#                 print(f"💬 Text message: {text}")

#         else:
#             print("⚠️ No messages in payload.")

#     except Exception as e:
#         print("❌ Error while processing message:", e)

#     return JSONResponse(content={"status": "received"})


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
            phone_number_id = value["metadata"]["phone_number_id"]

            if msg_type == "text":
                text = message["text"]["body"]
                print(f"💬 Text message from {sender}: {text}")

            elif msg_type == "audio":
                media_id = message["audio"]["id"]
                print(f"🎧 Voice message received from {sender} — Media ID: {media_id}")
                # Step 2: download this media_id next

    except Exception as e:
        print("❌ Error while processing message:", e)

    return JSONResponse({"status": "received"})

