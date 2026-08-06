import google.generativeai as genai
from openai import AsyncOpenAI
from core.config import settings
from prompts import SYSTEM_PROMPT

# Configure Gemini for Embeddings
if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)

# Configure OpenRouter client
openrouter_client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=settings.OPENROUTER_API_KEY,
)

async def generate_embedding(text: str) -> list[float]:
    """Generates an embedding vector for the given text using Gemini."""
    if not settings.GEMINI_API_KEY:
        print("WARNING: GEMINI_API_KEY is not set. Using dummy embedding.")
        return [0.0] * 768 # Gemini text-embedding-004 is 768 dimensions usually
        
    try:
        # text-embedding-004 is the recommended model
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=text,
            task_type="retrieval_query",
        )
        return result['embedding']
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return [0.0] * 768

async def generate_response(query: str, context: list[str], chat_history: str = "") -> str:
    """Generates a response from the LLM using the hermeneutic prompt and retrieved context."""
    if not settings.OPENROUTER_API_KEY:
        return "Mohon maaf, API Key OpenRouter belum dikonfigurasi."

    context_str = "\n---\n".join(context)
    formatted_system_prompt = SYSTEM_PROMPT.format(context=context_str, chat_history=chat_history)

    try:
        response = await openrouter_client.chat.completions.create(
            model="poolside/laguna-s-2.1:free",
            messages=[
                {"role": "system", "content": formatted_system_prompt},
                {"role": "user", "content": query}
            ],
            extra_headers={
                "HTTP-Referer": "http://localhost:3000",
                "X-Title": "Hermeneutic AI Tutor",
            }
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error calling LLM: {e}")
        return "Maaf, sistem sedang mengalami gangguan saat mencoba menjawab."
