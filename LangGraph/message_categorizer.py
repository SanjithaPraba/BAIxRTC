import json
from langchain_together import ChatTogether
from langchain.prompts import ChatPromptTemplate
from pathlib import Path
from dotenv import load_dotenv
import os

# Load API Key
load_dotenv()
api_key = os.getenv("TOGETHER_API_KEY")

# Ensure API key is set
if not api_key:
    raise ValueError("TOGETHER_API_KEY is missing. Please check your .env file.")

class MessageCategorizer:
    def __init__(self, categories_path: Path):
        with open(categories_path, 'r') as f:
            self.categories = json.load(f)

        self.llm = ChatTogether(
            together_api_key=api_key,
            model="mistralai/Mixtral-8x7B-Instruct-v0.1"
        )

    def classify(self, message: str) -> str:
        if not self.is_question_or_request(message):
            return "Not a question"

        category_list = "\n".join(f"- {c}" for c in self.categories)
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an assistant that classifies questions into predefined support categories."),
            ("human", f"""Here are the allowed categories:
    {category_list}

    Classify this question into one of those categories. Only return the category name.

    Message: {message}
    """)
        ])
        chain = prompt | self.llm
        response = chain.invoke({})
        return response.content.strip()

    def is_question_or_request(self, message: str) -> bool:
        prompt = ChatPromptTemplate.from_messages([
            ("system",
             "You are an assistant helping classify support messages. Decide whether the message is asking a question or requesting help. Respond only with 'Yes' or 'No'."),
            ("human", f"Message: \"{message}\"")
        ])
        chain = prompt | self.llm
        response = chain.invoke({})
        return response.content.strip().lower().startswith("yes")

