# Calendar Bot

This project is an helper whatsapp bot that that extracts event details from messages using a language model.
The LLM is pretty lightweight so you can even run it on you local computer.

## Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd calendar-bot
   ```

2. **Create and activate a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install the required packages**
   ```bash
   pip install -r requirements.txt
   ```

## Running the Server

To start the FastAPI server, run:

```bash
python server/server.py
```

Alternatively, you can use `uvicorn` directly:

```bash
uvicorn server.server:app --host 0.0.0.0 --port 8001
```

## Testing the Endpoint

You can test the `/extract_event/` endpoint using `curl`:

```bash
curl -X POST "http://127.0.0.1:8001/extract_event/" \
     -H "Content-Type: application/json" \
     -d '{"message": "Let's meeto tomorrow for a coffee at 14:00"}'
```

Replace `"Your event message here"` with the actual message you want to test.

## Dependencies

- FastAPI
- Pydantic
- Transformers
- Torch
- Dateparser

## License

This project is licensed under the MIT License. 