"""
Configuration management for the API
All settings loaded from environment variables with defaults
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Ollama Configuration - Using proper network URL (not localhost)
    # In production, this could be a service name like "ollama-service:11434"
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama:11434")  # Docker service name
    
    # Alternative: Use IP if needed
    # OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://192.168.1.100:11434")
    
    # Model name from Hugging Face / Ollama
    MODEL_NAME = os.getenv("MODEL_NAME", "hf.co/LiquidAI/LFM2.5-1.2B-Instruct-GGUF:q4_k_m")
    
    # API Settings
    API_TITLE = os.getenv("API_TITLE", "Simple Liquid LFM Chat")
    API_VERSION = os.getenv("API_VERSION", "1.0.0")
    
    # Network timeout settings
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", 30))
    
    # Model parameters
    TEMPERATURE = float(os.getenv("TEMPERATURE", 0.7))
    TOP_K = int(os.getenv("TOP_K", 50))
    REPEAT_PENALTY = float(os.getenv("REPEAT_PENALTY", 1.05))

# Create a singleton instance
config = Config()