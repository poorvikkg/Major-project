from groq import AsyncGroq
from backend.config import settings

class LLMService:
    def __init__(self):
        # The client will pick up GROQ_API_KEY from environment if available
        # or we explicitly pass it.
        api_key = settings.GROQ_API_KEY
        if not api_key or api_key == "your_groq_api_key_here":
            print("WARNING: GROQ_API_KEY is not set or is the default. Calls to Groq will fail.")
        
        self.client = AsyncGroq(api_key=api_key)
        self.model = settings.LLM_MODEL
        
    async def generate_response(self, prompt: str, system_prompt: str = "") -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = await self.client.chat.completions.create(
                messages=messages,
                model=self.model,
                temperature=0.2, # Keep it low for factual responses
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error connecting to LLM: {str(e)}"

# Singleton instance
llm_service = LLMService()
