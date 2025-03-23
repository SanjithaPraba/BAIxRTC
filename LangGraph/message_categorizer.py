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

    def classify_batch(self, messages: list[str]) -> list[str]:
        if not messages:
            return []

        # Format messages as a numbered list
        numbered_messages = "\n".join([f"{i+1}. {msg}" for i, msg in enumerate(messages)])
        category_list = "\n".join(f"- {c}" for c in self.categories)

        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""You are a support assistant categorizing Slack messages. 
Your job is to classify each message into one of the following categories:

{category_list}

Return only the category name for each message, in order. If the message is not a question, respond with "Not a question".

"""),
            ("human", f"""Classify these messages:

{numbered_messages}

Return format:
1. <Category>
2. <Category>
...
""")
        ])

        chain = prompt | self.llm
        response = chain.invoke({})
        raw_output = response.content.strip().split("\n")

        # Clean up and return a list of categories
        return [line.split(". ", 1)[-1].strip() for line in raw_output if line]

