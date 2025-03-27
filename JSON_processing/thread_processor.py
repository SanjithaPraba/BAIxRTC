import json
import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from langchain_together import ChatTogether
from langchain.prompts import ChatPromptTemplate

load_dotenv()
api_key = os.getenv("TOGETHER_API_KEY")
if not api_key:
    raise ValueError("TOGETHER_API_KEY is missing. Please check your .env file.")

def clean_message(message: dict, category: str) -> dict:
    """Extract essential message data and assign a category."""
    return {
        "text": message.get("text", ""),
        "user": message.get("user", ""),
        "ts": message.get("ts", ""),
        "team": message.get("team", ""),
        "category": category
    }

def batch_categorize_messages(processed_json_file_path: str, categories_file: str, batch_size: int = 500) -> List[str]:
    """
    Process messages in batches and return a flat list of categories.
    The categories are generated in the same order as the messages.
    """
    with open(processed_json_file_path, 'r') as f:
        messages = json.load(f)

    with open(categories_file, 'r') as f:
        categories = json.load(f)

    # Get list of allowed categories.
    category_values = categories["categories"] if isinstance(categories, dict) else categories
    category_list = "\n".join(f"- {c}" for c in category_values)

    llm = ChatTogether(
        together_api_key=api_key,
        model="mistralai/Mixtral-8x7B-Instruct-v0.1"
    )

    all_categories = []
    total_messages = len(messages)

    for i in range(0, total_messages, batch_size):
        batch = messages[i:min(i + batch_size, total_messages)]
        texts = [msg.get("text", "") for msg in batch]

        numbered_messages = "\n".join([f"{idx + 1}. {text}" for idx, text in enumerate(texts)])
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""You are a support assistant categorizing Slack messages.
Classify each message into one of the following categories:

{category_list}

Return only the category name for each message, in order. If a message does not fit any category, respond with "other" and what the message could be potentially related to.
"""),
            ("human", f"""Classify these messages:

{numbered_messages}

Return format:
1. <Category>
2. <Category>
...
""")
        ])

        chain = prompt | llm
        response = chain.invoke({})
        raw_output = response.content.strip().split("\n")
        batch_categories = [line.split(". ", 1)[-1].strip() for line in raw_output if line]
        
        # Append the categories for this batch
        all_categories.extend(batch_categories)

    return all_categories

def process_channel_data(input_dir: Path, output_dir: Path, categories_file: str, batch_size: int = 500):
    """
    For each JSON file in input_dir, process the messages in batches,
    add a category attribute, and write out the updated messages.
    """
    for input_file in input_dir.glob("**/*.json"):
        print(f"Processing {input_file}")
        try:
            with open(input_file, 'r') as f:
                messages = json.load(f)
            if not isinstance(messages, list):
                print(f"Skipping {input_file}: Data is not a list")
                continue

            # Build a list of categories (in order) for all messages in the file.
            generated_categories = batch_categorize_messages(str(input_file), categories_file, batch_size)

            # In case the number of generated categories doesn't match, default missing ones to "other"
            if len(generated_categories) < len(messages):
                generated_categories.extend(["other"] * (len(messages) - len(generated_categories)))
            elif len(generated_categories) > len(messages):
                generated_categories = generated_categories[:len(messages)]

            # Build updated messages by zipping messages and generated categories.
            updated_messages = [
                clean_message(msg, category)
                for msg, category in zip(messages, generated_categories)
            ]

            # Save updated messages to output file.
            output_file = output_dir / input_file.name
            with open(output_file, 'w') as f:
                json.dump(updated_messages, f, indent=2)
            print(f"Saved categorized messages to {output_file}")
        except Exception as e:
            print(f"Error processing {input_file}: {e}")

def main():
    base_input_dir = Path("/Users/sanjitha/Documents/BAIxRTC/JSON_processing/data/processed")
    base_output_dir = Path("/Users/sanjitha/Documents/BAIxRTC/JSON_processing/data/categorized")
    categories_file = "/Users/sanjitha/Documents/BAIxRTC/JSON_processing/categories.json"

    print(f"Current working directory: {Path.cwd()}")
    
    if not base_input_dir.exists():
        print(f"Error: Input directory not found at {base_input_dir}")
        return

    base_output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Processing data from {base_input_dir}")
    process_channel_data(base_input_dir, base_output_dir, categories_file)
    print(f"Categorized data saved to {base_output_dir}")

if __name__ == "__main__":
    main()
