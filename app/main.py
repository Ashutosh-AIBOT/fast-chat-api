"""
Minimal FastAPI + Liquid LFM 2.5-1.2B Chat
Using separate config file with proper network URLs
"""

import time
import httpx
import json
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# Import config from separate file
from config import config

# Create FastAPI app using config values
app = FastAPI(
    title=config.API_TITLE,
    version=config.API_VERSION
)

# ========== REQUEST/RESPONSE MODELS ==========
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    model: str
    time_taken: float

# ========== HEALTH CHECK ==========
@app.get("/health")
async def health():
    """Health check that verifies Ollama connection"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{config.OLLAMA_HOST}/api/tags")
            if r.status_code == 200:
                models = r.json().get("models", [])
                model_names = [m["name"] for m in models]
                return {
                    "status": "healthy",
                    "ollama": "connected",
                    "ollama_url": config.OLLAMA_HOST,  # Shows which URL is being used
                    "available_models": model_names,
                    "using_model": config.MODEL_NAME
                }
    except Exception as e:
        return {
            "status": "degraded",
            "ollama": "not reachable",
            "ollama_url": config.OLLAMA_HOST,
            "error": str(e),
            "message": "Check if Ollama is running at the configured URL"
        }
    
    return {
        "status": "degraded",
        "ollama": "not reachable",
        "ollama_url": config.OLLAMA_HOST
    }

# ========== SIMPLE CHAT ENDPOINT ==========
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Simple chat endpoint - sends message to LLM and returns response
    """
    start_time = time.time()
    
    # Format prompt for Liquid LFM
    prompt = f"<|im_start|>user\n{request.message}<|im_end|>\n<|im_start|>assistant\n"
    
    try:
        # Call Ollama API using URL from config
        async with httpx.AsyncClient(timeout=config.REQUEST_TIMEOUT) as client:
            response = await client.post(
                f"{config.OLLAMA_HOST}/api/generate",
                json={
                    "model": config.MODEL_NAME,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": config.TEMPERATURE,
                        "top_k": config.TOP_K,
                        "repeat_penalty": config.REPEAT_PENALTY
                    }
                }
            )
            
            if response.status_code != 200:
                return ChatResponse(
                    response=f"Error: {response.status_code} - {response.text}",
                    model=config.MODEL_NAME,
                    time_taken=time.time() - start_time
                )
            
            result = response.json()
        
        return ChatResponse(
            response=result["response"],
            model=config.MODEL_NAME.split("/")[-1],
            time_taken=round(time.time() - start_time, 2)
        )
    
    except Exception as e:
        return ChatResponse(
            response=f"Connection error: {str(e)}",
            model=config.MODEL_NAME,
            time_taken=time.time() - start_time
        )

# ========== STREAMING CHAT ==========
@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Streaming version - sends tokens one by one
    """
    prompt = f"<|im_start|>user\n{request.message}<|im_end|>\n<|im_start|>assistant\n"
    
    async def generate():
        try:
            async with httpx.AsyncClient(timeout=config.REQUEST_TIMEOUT) as client:
                async with client.stream(
                    "POST",
                    f"{config.OLLAMA_HOST}/api/generate",
                    json={
                        "model": config.MODEL_NAME,
                        "prompt": prompt,
                        "stream": True,
                        "options": {
                            "temperature": config.TEMPERATURE,
                            "top_k": config.TOP_K,
                        }
                    }
                ) as response:
                    async for line in response.aiter_lines():
                        if line:
                            data = json.loads(line)
                            if "response" in data:
                                yield data["response"]
                            if data.get("done", False):
                                break
        except Exception as e:
            yield f"\n[Error: {str(e)}]"
    
    return StreamingResponse(generate(), media_type="text/plain")

# ========== ROOT ENDPOINT ==========
@app.get("/")
async def root():
    """API information"""
    return {
        "name": config.API_TITLE,
        "version": config.API_VERSION,
        "model": config.MODEL_NAME,
        "ollama_url": config.OLLAMA_HOST,  # Shows which URL is configured
        "endpoints": {
            "GET /": "This information",
            "GET /health": "Health check with connection status",
            "POST /chat": "Send a message (returns full response)",
            "POST /chat/stream": "Stream response in real-time"
        },
        "docs": "/docs",
        "note": "No authentication required - simple Q&A"
    }