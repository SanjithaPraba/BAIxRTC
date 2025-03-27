import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

from dotenv import load_dotenv
import os

# --- Categorization Helper (embedded from batch_categorizer.py) ---
from langchain_together import ChatTogether
from langchain.prompts import ChatPromptTemplate

load_dotenv()
api_key = os.getenv("TOGETHER_API_KEY")
if not api_key:
    raise ValueError("TOGETHER_API_KEY is missing. Please check your .env file.")

def categorize_messages_in_batches(messages: List[dict], categories_file, batch_size: int = 500) -> List[dict]:
    """
    Categorizes a list of Slack message dictionaries in batches using Mistral API calls.

    Parameters:
        messages (list[dict]): List of message dictionaries with a 'text' key.
        categories_file (str or Path): Path to a JSON file containing a list of categories.
        batch_size (int): The number of messages to process per API call (default is 500).

    Returns:
        list[dict]: The original list of messages with an added "category" key for each message.
    """
    # Load categories from the provided file.
    with open(Path(categories_file), 'r') as f:
        categories = json.load(f)

    # Expect categories.json to be either a list or an object with a "categories" key.
    if isinstance(categories, dict) and "categories" in categories:
        category_values = categories["categories"]
    elif isinstance(categories, list):
        category_values = categories
    else:
        raise ValueError("categories.json must be a list or contain a 'categories' key with a list.")

    # Build the category list string (one category per line, preceded by a hyphen).
    category_list = "\n".join(f"- {c}" for c in category_values)

    # Initialize the LLM.
    llm = ChatTogether(
        together_api_key=api_key,
        model="mistralai/Mixtral-8x7B-Instruct-v0.1"
    )

    categorized_messages = []
    for i in range(0, len(messages), batch_size):
        batch = messages[i:i+batch_size]
        texts = [msg.get("text", "") for msg in batch]
        
        numbered_messages = "\n".join([f"{idx+1}. {text}" for idx, text in enumerate(texts)])
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""You are a support assistant categorizing Slack messages.
Classify each message into one of the following categories:

{category_list}

Return only the category name for each message, in order. If a message does not fit any category, respond with "other".
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
        
        for msg, cat in zip(batch, batch_categories):
            msg["category"] = cat
            categorized_messages.append(msg)
    return categorized_messages

# --- Original Thread Processing Functions ---
def clean_message(message: dict) -> dict:
    """Extract only essential message data."""
    return {
        "text": message.get("text", ""),
        "user": message.get("user", ""),
        "ts": message.get("ts", ""),
        "team": message.get("team", "")
    }

def group_messages_by_thread(rtc_data):
    # Define subtypes to exclude.
    EXCLUDED_SUBTYPES = {
        'channel_join',
        'channel_leave', 
        'channel_purpose',
        'channel_topic',
        'channel_name',
        'channel_archive',
        'channel_unarchive',
        'bot_message'
    }
    
    threads = []
    
    for message in rtc_data:
        # Skip if message is not a dictionary.
        if not isinstance(message, dict):
            print(f"Skipping invalid message format: {message}")
            continue
            
        # Skip system messages and messages with excluded subtypes.
        if message.get("subtype") in EXCLUDED_SUBTYPES:
            continue
            
        thread_ts = message.get("thread_ts")
        message_ts = message.get("ts")
        
        # Skip if message doesn't have a timestamp.
        if not message_ts:
            continue
        
        # If this is a parent message (start of a thread).
        if not thread_ts or thread_ts == message_ts:
            thread_replies = []
            
            # If message has replies, collect them.
            if message.get("replies"):
                # Find all reply messages in the rtc_data.
                for reply_info in message["replies"]:
                    reply_ts = reply_info["ts"]
                    # Find the full reply message in rtc_data.
                    for reply_msg in rtc_data:
                        if isinstance(reply_msg, dict) and reply_msg.get("ts") == reply_ts:
                            thread_replies.append(clean_message(reply_msg))
                            break
            
            # Create clean thread object.
            thread = {
                "thread_ts": message_ts,
                "message": clean_message(message),
                "replies": thread_replies,
                "reply_count": len(thread_replies)
            }
            threads.append(thread)
    
    return threads

def process_channel_data(input_dir: Path, output_dir: Path):
    """Process all channel data, group threads by channel, and categorize messages."""
    # Dictionary to store threads by channel.
    channel_threads: Dict[str, List] = defaultdict(list)
    
    # Process each JSON file in the input directory.
    for input_file in input_dir.glob("**/*.json"):
        # Get channel name from the parent directory.
        channel = input_file.parent.name
        print(f"Processing {input_file}")
        
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                rtc_data = json.load(f)
                if not isinstance(rtc_data, list):
                    print(f"Skipping {input_file}: Data is not a list")
                    continue
                # Group messages into threads.
                threads = group_messages_by_thread(rtc_data)
                channel_threads[channel].extend(threads)
        except json.JSONDecodeError as e:
            print(f"Error reading {input_file}: {e}")
        except Exception as e:
            print(f"Error processing {input_file}: {e}")
    
    # Create output directory if it doesn't exist.
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # For each channel, categorize messages and save threads.
    for channel, threads in channel_threads.items():
        print(f"Processing categorization for channel: {channel}")
        # Extract all messages (parent + replies) from threads.
        messages = []
        for thread in threads:
            messages.append(thread["message"])
            for reply in thread.get("replies", []):
                messages.append(reply)
        print(f"Total messages to categorize in channel {channel}: {len(messages)}")
        
        # Categorize messages using the embedded helper.
        categorize_messages_in_batches(
            messages, 
            "/Users/sanjitha/Documents/BAIxRTC/JSON_processing/categories.json",
            batch_size=500
        )
        # (Since the message objects are mutable, threads are updated automatically.)
        
        # Update each thread with a top-level "category" attribute from the parent message.
        for thread in threads:
            thread["category"] = thread["message"].get("category", "other")
        
        output_file = output_dir / f"{channel}_threads.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(threads, f, indent=2)
        print(f"Saved {len(threads)} threads with categories for channel {channel}")

def main():
    base_input_dir = Path("/Users/sanjitha/Documents/BAIxRTC/JSON_processing/data/rtc_data")
    base_output_dir = Path("/Users/sanjitha/Documents/BAIxRTC/JSON_processing/data/channel_threads")
    print(f"Current working directory: {Path.cwd()}")
    
    if not base_input_dir.exists():
        print(f"Error: Input directory not found at {base_input_dir}")
        return
    
    print(f"Processing data from {base_input_dir}")
    process_channel_data(base_input_dir, base_output_dir)
    print(f"Thread data saved to {base_output_dir}")

if __name__ == "__main__":
    main()