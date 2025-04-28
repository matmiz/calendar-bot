import datetime
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from llama_cpp import Llama

import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

llm = Llama(model_path="models/dictalm2.0-instruct.Q4_K_M.gguf", n_gpu_layers=1)
def runLLM(prompt):
    return llm(prompt, max_tokens=60, temperature=0.0)["choices"][0]["text"]


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
        <system>
        You are a JSON-only extractor.  
        Return **one single JSON object** and nothing else. Do NOT add any extra text outside the JSON structure.
        </system>

        <user>
        Extract event details from the following message: "{text}"
        When extracting the event details, take into account that today's date is {datetime.datetime.now().strftime('%Y-%m-%d')} in a YYYY-MM-DD format.

        Please output strictly in JSON format with this structure, while the title is in Hebrew:
        {{
        "title": "<event title>",
        "date": "<YYYY-MM-DD>",
        "time": "<HH:MM>"
        }}


        </user>
        """

        logger.info(f"Processing input text: {text}")

        response = runLLM(prompt)

        logger.info(f"Raw model response: {response}")

        # Extract JSON from response
        try:
            json_start = response.index("{")
            json_end = response.rindex("}") + 1
            json_data = json.loads(response[json_start:json_end])
            logger.info(f"Server response: {json_data}")
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
        logger.error(event_data)
        raise HTTPException(status_code=500, detail=event_data["error"])
    return event_data

# Run the server
if __name__ == "__main__":
    import uvicorn
    PORT = int(os.getenv("PORT", 8001))
    logger.info("Starting FastAPI server...")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
