from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class AgentRequest(BaseModel):
    message: str


@app.post("/api/agent/run")
async def run_agent(request: AgentRequest):
    return {"message": f"Received message: {request.message}", "status": "received"}


@app.get("/health")
async def health():
    return {"status": "ok"}
