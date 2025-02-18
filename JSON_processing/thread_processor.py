import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

def clean_message(message: dict) -> dict:
    """Extract only essential message data."""
    return {
        "text": message.get("text", ""),
        "user": message.get("user", ""),
        "ts": message.get("ts", ""),
        "team": message.get("team", "")
    }

def group_messages_by_thread(rtc_data):
    # Define subtypes to exclude
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
        # Skip if message is not a dictionary
        if not isinstance(message, dict):
            print(f"Skipping invalid message format: {message}")
            continue
            
        # Skip system messages and messages with excluded subtypes
        if message.get("subtype") in EXCLUDED_SUBTYPES:
            continue
            
        thread_ts = message.get("thread_ts")
        message_ts = message.get("ts")
        
        # Skip if message doesn't have a timestamp
        if not message_ts:
            continue
        
        # If this is a parent message (start of a thread)
        if not thread_ts or thread_ts == message_ts:
            thread_replies = []
            
            # If message has replies, collect them
            if message.get("replies"):
                # Find all reply messages in the rtc_data
                for reply_info in message["replies"]:
                    reply_ts = reply_info["ts"]
                    # Find the full reply message in rtc_data
                    for reply_msg in rtc_data:
                        if isinstance(reply_msg, dict) and reply_msg.get("ts") == reply_ts:
                            thread_replies.append(clean_message(reply_msg))
                            break
            
            # Create clean thread object
            thread = {
                "thread_ts": message_ts,
                "message": clean_message(message),
                "replies": thread_replies,
                "reply_count": len(thread_replies)
            }
            threads.append(thread)
    
    return threads

def process_channel_data(input_dir: Path, output_dir: Path):
    """Process all channel data and group threads by channel."""
    # Dictionary to store threads by channel
    channel_threads: Dict[str, List] = defaultdict(list)
    
    # Process each JSON file in the input directory
    for input_file in input_dir.glob("**/*.json"):
        # Get channel name from the parent directory
        channel = input_file.parent.name
        print(f"Processing {input_file}")
        
        # Read input data
        try:
            with open(input_file, 'r') as f:
                rtc_data = json.load(f)
                if not isinstance(rtc_data, list):
                    print(f"Skipping {input_file}: Data is not a list")
                    continue
                # Group messages into threads
                threads = group_messages_by_thread(rtc_data)
                # Add threads to channel collection
                channel_threads[channel].extend(threads)
        except json.JSONDecodeError as e:
            print(f"Error reading {input_file}: {e}")
        except Exception as e:
            print(f"Error processing {input_file}: {e}")
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save threads grouped by channel
    for channel, threads in channel_threads.items():
        output_file = output_dir / f"{channel}_threads.json"
        with open(output_file, 'w') as f:
            json.dump(threads, f, indent=2)
        print(f"Saved {len(threads)} threads for channel {channel}")

def main():
    base_input_dir = Path("JSON_processing/data/rtc_data")
    base_output_dir = Path("JSON_processing/data/channel_threads")
    
    if not base_input_dir.exists():
        print(f"Error: Input directory not found at {base_input_dir}")
        return
    
    print(f"Processing data from {base_input_dir}")
    process_channel_data(base_input_dir, base_output_dir)
    print(f"Thread data saved to {base_output_dir}")

if __name__ == "__main__":
    main()
