#!/usr/bin/env python3
"""
Simple test script to verify Grok API integration
"""
import os
from openai import OpenAI

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Initialize OpenAI client with Grok settings
api_key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OPENAI_BASE_URL")
model = os.getenv("OPENAI_MODEL")

print(f"🔧 Testing Grok API Integration")
print(f"   API Key: {api_key[:20]}..." if api_key else "   API Key: Not set")
print(f"   Base URL: {base_url}")
print(f"   Model: {model}")
print()

if not api_key:
    print("❌ OPENAI_API_KEY not set!")
    exit(1)

# Create client
client = OpenAI(api_key=api_key, base_url=base_url)

# Test simple completion
print("📝 Testing simple chat completion...")
try:
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful project management assistant."},
            {"role": "user", "content": "What are the key benefits of using AI in project portfolio management? Give me 3 brief points."}
        ],
        max_tokens=200
    )
    
    print("✅ Success! Grok responded:")
    print("-" * 50)
    print(response.choices[0].message.content)
    print("-" * 50)
    print(f"\n📊 Token usage: {response.usage.total_tokens} tokens")
    print(f"   Model used: {response.model}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)

print("\n✅ Grok API integration is working!")
