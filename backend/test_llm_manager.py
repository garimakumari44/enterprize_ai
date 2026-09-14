import asyncio
from dotenv import load_dotenv

load_dotenv()

from app.services.llm_manager import LLMManager


async def main():
    manager = LLMManager()

    print("PROVIDER:", manager.provider_name)
    print("MODEL:", manager.default_model)
    print("OPENROUTER REGISTERED:", "openrouter" in manager.providers)

    if "openrouter" in manager.providers:
        print(
            "PROVIDER TYPE:",
            type(manager.providers["openrouter"]).__name__,
        )

    response = await manager.chat(
        messages=[
            {
                "role": "user",
                "content": "Reply with exactly OPENROUTER_MANAGER_OK",
            }
        ],
        model="meta-llama/llama-3.3-70b-instruct",
        max_tokens=20,
    )

    print("CONTENT:", response.content)
    print("MODEL:", response.model)
    print("PROVIDER:", response.provider)


asyncio.run(main())
