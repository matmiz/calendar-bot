import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForCausalLM
import logging

import torch
import dateparser
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODEL_NAME = "tiiuae/falcon-7b-instruct"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForCausalLM.from_pretrained(MODEL_NAME, torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32)
# Move to GPU if available
device = "cuda" if torch.cuda.is_available() else "cpu"
model.to(device)


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
        Extract event details from the following message in Hebrew:
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
        outputs = model.generate(**inputs, max_length=200)
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
