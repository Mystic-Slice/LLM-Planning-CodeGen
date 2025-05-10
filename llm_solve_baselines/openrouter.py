import os
import dotenv
from openai import OpenAI

dotenv.load_dotenv()

def call_openrouter(model, messages):
    openai_client = OpenAI(
        base_url='https://openrouter.ai/api/v1',
        api_key=os.getenv("OPENROUTER_API_KEY")
    )

    response = openai_client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0,
    )
    response = response.choices[0].message.content

    return response