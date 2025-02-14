import os
import sys
import json
from tqdm import tqdm

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)


def get_data_path():
    """Get the path to the Slack data folder."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # Update path to include rtc_data subfolder
    return os.path.join(project_root, "data", "rtc_data")

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

def main():
    print("Starting data preprocessing...")
    
    # Get source and output paths
    source_dir = get_data_path()
    output_dir = os.path.join(os.path.dirname(source_dir), "processed")  # Save processed data in data/processed
    
    print(f"Reading data from: {source_dir}")
    print(f"Output will be saved to: {output_dir}")
    
    # Verify the source directory exists
    if not os.path.exists(source_dir):
        print(f"Error: Source directory not found at {source_dir}")
        exit(1)
        
    # Process the data
    processed_data = preprocess_slack_data(source_dir, output_dir)
    
    # Print summary of processed data
    print("\nProcessing complete!")
    for channel, messages in processed_data.items():
        print(f"Channel {channel}: {len(messages)} messages processed")

if __name__ == "__main__":
    main() 