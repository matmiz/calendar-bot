import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForCausalLM
import logging

import torch
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

is_mps = torch.backends.mps.is_available()  # True on M-series Macs
dtype   = torch.float16 if is_mps else torch.float32
# DictaLM ships with a custom config, so we allow remote code
MODEL_NAME = "dicta-il/dictalm2.0-instruct"
tokenizer = AutoTokenizer.from_pretrained(
    MODEL_NAME, trust_remote_code=True, use_fast=False
)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    torch_dtype=dtype,
    device_map="auto",          # puts weights on the M-series GPU
    trust_remote_code=True
)

device = "mps" if is_mps else "cpu"


app = FastAPI()
@app.on_event("startup")
async def startup_event():
    port = os.getenv("PORT", "Unknown (VSCode may override)")
    logger.info(f"🚀 Server is running and listening on http://127.0.0.1:{port}")

@app.get("/")
def read_root():
    return {"message": "Server is running!"}
# Input schema
class MessageInput(BaseModel):
    message: str

# Function to extract event details
def extract_event_details(text):
    try:   # Find the first { and last } in the response
        prompt = f"""
        Extract event details from the following message:
        "{text}"

        Respond strictly in JSON format with this structure:
        {{
            "title": "<event title>",
            "date": "<YYYY-MM-DD>",
            "time": "<HH:MM>"
        }}

        Do NOT add any extra text outside this JSON structure.
        """

        logger.info(f"Processing input text: {text}")
        
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        logger.info(f"1")
        outputs = model.generate(**inputs, max_length=200)
        logger.info(f"2")
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)

        logger.info(f"Raw model response: {response}")

        # Extract JSON from response
        try:
            json_start = response.index("{")
            json_end = response.rindex("}") + 1
            json_data = json.loads(response[json_start:json_end])
            return json_data
        except Exception as e:
            return {
                "error": "Could not parse response",
                "details": str(e),
                "raw_output": response
            }
    except Exception as e:
        logger.error(e)


@app.post("/extract_event/")
async def extract_event(data: MessageInput):
    event_data = extract_event_details(data.message)
    if "error" in event_data:
        raise HTTPException(status_code=500, detail=event_data["error"])
    return event_data

# Run the server
if __name__ == "__main__":
    import uvicorn
    PORT = int(os.getenv("PORT", 8001))
    logger.info("Starting FastAPI server...")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
