import dotenv from 'dotenv'; 
import express from 'express';
import bodyParser from 'body-parser';
import twilio from 'twilio';

dotenv.config();
const app = express();
app.use(bodyParser.urlencoded({ extended: false }));

// simple signature check (optional in sandbox)
const auth = twilio.validateRequest;
const pending = {};

function addToCalendar(message, req, res){
    const twiml = new twilio.twiml.MessagingResponse();
    if(message === 'Y') {
        console.log(pending[req.body.From]);
        twiml.message("אירוע נוסף ללוח השנה");
    }
    else if(message === 'N') {
        pending[req.body.From] = null;
        twiml.message("נסה לשלוח שנית");
    }
    else {
        twiml.message("אנא תענה רק בY או N");
    }
    res.type('text/xml').send(twiml.toString());
}
app.post('/whatsapp', async (req, res) => {
  const msg = req.body.Body || '';
  let event;
  try {
    if(msg === 'Y' || msg === 'N') {
        return addToCalendar(msg, req, res);
    }
    const r = await fetch('http://localhost:8001/extract_event/', {
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: msg }), 
    method: "POST"
    });
    event = await r.json();                     // {title,date,time}
  } catch(e) {
     console.error(e);
  }
  const twiml = new twilio.twiml.MessagingResponse();
  if (event?.date && event?.time) {
    twiml.message(
      `🍀 אירוע: "${event.title}"\n` +
      `📅 תאריך: ${event.date}\n⏰ שעה: ${event.time}\n\n` +
      `להוסיף ליומן? השב Y או N`
    );
    // store event in memory keyed by From number
    pending[req.body.From] = event;
  } else {
        twiml.message("לא הצלחתי להבין תאריך/שעה 🤖");
  }
  res.type('text/xml').send(twiml.toString());
});

const server = app.listen(process.env.PORT, () =>
  console.log(`Bot up on :${process.env.PORT}`)
);
server.headersTimeout = 1200000;
