import os
import time
from fastapi import FastAPI, Request
import uvicorn

app = FastAPI(title="Agent on Render")

# Mock LLM trực tiếp trong file để tránh lỗi import
def mock_ask(question: str):
    return f"Đây là câu trả lời giả lập cho câu hỏi: {question}"

@app.get("/")
def root():
    return {"message": "AI Agent running on Render!"}

@app.post("/ask")
async def ask_agent(request: Request):
    try:
        body = await request.json()
        question = body.get("question", "hello")
        return {
            "question": question,
            "answer": mock_ask(question),
            "platform": "Render",
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/health")
def health():
    return {"status": "ok", "platform": "Render"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
