from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import dateparser
import json

MODEL_NAME = "google/mt5-base"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
#torch.cuda.is_available() => checks if a GPU is avaiable
model = AutoModelForCausalLM.from_pretrained(MODEL_NAME, torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32)

app = FastAPI()

# Input schema
class MessageInput(BaseModel):
    message: str

# Function to extract event details
def extract_event_details(text):
    prompt = f"""
    Extract the event details from the following message:
    "{text}"

    Return the output in JSON format:
    {{
      "title": "<event title>",
      "date": "<YYYY-MM-DD>",
      "time": "<HH:MM>"
    }}
    """
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    outputs = model.generate(**inputs, max_length=200)
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)

    # Extract JSON from response
    try:
        json_data = json.loads(response[response.index("{"):response.rindex("}")+1])
        return json_data
    except:
        return {"error": "Could not parse response"}

@app.post("/extract_event/")
async def extract_event(data: MessageInput):
    event_data = extract_event_details(data.message)
    return event_data

# Run the server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
