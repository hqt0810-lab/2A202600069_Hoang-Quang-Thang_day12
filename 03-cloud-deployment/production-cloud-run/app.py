import os
import time
from fastapi import FastAPI
import uvicorn
from utils.mock_llm import ask

app = FastAPI(title="Agent on Cloud Run")

@app.get("/")
def root():
    return {"message": "Hello from Google Cloud Run!"}

@app.post("/ask")
def ask_agent(question: str):
    return {"answer": ask(question)}

@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    # Cloud Run tự động inject PORT
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
