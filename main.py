from fastapi import FastAPI, Request, Header, Depends
from chatbot import *
app = FastAPI()

@app.post('/chat')
async def chat(request: Request):
    json = await request.json()
    print(json)
    return {"response": invoke_chat_bot(json['chat'])}

@app.post('/chat1')
def chat(request: Request):
    return {"response": invoke_chat_bot("show me the scheduled events")}

@app.post('/chat2')
def chat(request: Request):
    return {"response": invoke_chat_bot("cancel my event at 8pm today")}

    
