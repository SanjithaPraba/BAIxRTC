import pandas as pd
import json
import os
from typing import List, Dict
import re
from collections import defaultdict
from tqdm import tqdm

class SlackDataProcessor:
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        
    def _clean_message(self, text: str) -> str:
        # Remove URLs
        text = re.sub(r'http\S+', '', text)
        # Remove user mentions
        text = re.sub(r'<@[A-Za-z0-9]+>', '', text)
        # Remove special characters
        text = re.sub(r'[^\w\s.,!?]', ' ', text)
        # Remove extra whitespace
        text = ' '.join(text.split())
        return text.strip()
    
    def process_channel_directory(self, channel_dir: str, channel_name: str) -> List[Dict]:
        processed_messages = []
        channel_messages = []
        
        # Process all JSON files in the channel directory
        for file in os.listdir(channel_dir):
            if file.endswith('.json'):
                file_path = os.path.join(channel_dir, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    try:
                        messages = json.load(f)
                        channel_messages.extend(messages)
                    except json.JSONDecodeError:
                        print(f"Error reading {file_path}")
                        continue
        
        # Write raw channel data
        with open('raw_messages.txt', 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*80}\n")
            f.write(f"Channel: {channel_name}\n")
            f.write(f"Total messages in channel: {len(channel_messages)}\n")
            f.write(f"{'='*80}\n")
        
        # Process all messages for this channel
        for msg in channel_messages:
            if 'subtype' not in msg and 'text' in msg:
                cleaned_text = self._clean_message(msg['text'])
                if len(cleaned_text) > 50:  # Filter out very short messages
                    processed_msg = {
                        'text': cleaned_text,
                        'timestamp': msg.get('ts', ''),
                        'channel': channel_name,
                        'user': msg.get('user', '')
                    }
                    processed_messages.append(processed_msg)
        
        # Write processed channel data
        with open('processed_messages.txt', 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*80}\n")
            f.write(f"Channel: {channel_name}\n")
            f.write(f"Processed messages: {len(processed_messages)}\n")
            f.write(f"{'='*80}\n\n")
            for msg in processed_messages[:5]:  # Show sample of processed messages
                f.write(f"Sample message:\n")
                f.write(f"Text: {msg['text']}\n")
                f.write(f"Timestamp: {msg['timestamp']}\n")
                f.write(f"User: {msg['user']}\n")
                f.write(f"{'-'*40}\n")
            if len(processed_messages) > 5:
                f.write(f"\n... and {len(processed_messages)-5} more messages\n")
        
        return processed_messages
    
    def process_all_channels(self) -> pd.DataFrame:
        all_messages = []
        channels_data = defaultdict(list)
        
        # First, group by channels
        for root, dirs, files in os.walk(self.data_dir):
            for dir_name in dirs:
                channel_path = os.path.join(root, dir_name)
                messages = self.process_channel_directory(channel_path, dir_name)
                channels_data[dir_name] = messages
                all_messages.extend(messages)
        
        # Write summary
        with open('processing_summary.txt', 'w', encoding='utf-8') as f:
            f.write("Processing Summary\n")
            f.write("="*50 + "\n\n")
            for channel, messages in channels_data.items():
                f.write(f"Channel: {channel}\n")
                f.write(f"Messages processed: {len(messages)}\n")
                f.write(f"Unique users: {len(set(msg['user'] for msg in messages))}\n")
                f.write("-"*30 + "\n")
        
        return pd.DataFrame(all_messages)

def preprocess_slack_data(source_dir, output_dir):
    """
    Preprocess Slack data and save it in a structured format.
    
    Parameters:
        source_dir (str): Path to rtc_data directory containing channel folders
        output_dir (str): Path where processed data will be saved
    """
    print("\nStarting preprocessing...")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    print(f"Created output directory: {output_dir}")
    
    # Dictionary to store all processed messages by channel
    processed_data = {}
    
    # Folders to ignore
    ignore_folders = {'vector_store', 'processed', '.git', '__pycache__'}
    
    # Iterate through channel directories
    channels = [d for d in os.listdir(source_dir) 
               if os.path.isdir(os.path.join(source_dir, d)) 
               and d not in ignore_folders]
    
    print(f"\nFound {len(channels)} channels to process")
    
    for channel in tqdm(channels, desc="Processing channels"):
        channel_path = os.path.join(source_dir, channel)
        print(f"\nProcessing channel: {channel}")
        
        # Initialize channel data
        processed_data[channel] = []
        
        # Process all JSON files in the channel directory
        json_files = [f for f in os.listdir(channel_path) if f.endswith('.json')]
        print(f"Found {len(json_files)} JSON files in {channel}")
        
        for json_file in tqdm(json_files, desc=f"Processing {channel}", leave=False):
            file_path = os.path.join(channel_path, json_file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    messages = json.load(f)
                print(f"Successfully read {len(messages)} messages from {json_file}")
                
                # Clean and process messages
                cleaned_messages = []
                for msg in messages:
                    if not isinstance(msg, dict):
                        continue
                        
                    # Extract text content
                    text = msg.get('text', '')
                    
                    # Skip empty messages
                    if not text.strip():
                        continue
                        
                    cleaned_msg = {
                        'channel': channel,
                        'user': msg.get('user', 'unknown'),
                        'ts': msg.get('ts'),
                        'text': text.strip(),
                        'date': json_file.split('.')[0]  # Get date from filename
                    }
                    cleaned_messages.append(cleaned_msg)
                    
                processed_data[channel].extend(cleaned_messages)
                    
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
                
        # Save channel data
        if processed_data[channel]:
            channel_dir = os.path.join(output_dir, channel)
            os.makedirs(channel_dir, exist_ok=True)
            
            output_file = os.path.join(channel_dir, f"{channel}_processed.json")
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(processed_data[channel], f, indent=2, ensure_ascii=False)
            
            print(f"Processed {len(processed_data[channel])} messages for channel: {channel}")
    
    return processed_data
