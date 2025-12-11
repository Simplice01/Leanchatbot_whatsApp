import os
from dotenv import load_dotenv
from groq import Groq
import httpx

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Fix SSL sur Windows + compatibilité Render
http_client = httpx.Client(verify=False)

groq_client = Groq(
    api_key=GROQ_API_KEY,
    http_client=http_client
)

SYSTEM_PROMPT = """
Tu es LearnBot...
"""

def generate_ai_reply(message):
    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": message}
        ],
        temperature=0.7
    )

    return response.choices[0].message.content
