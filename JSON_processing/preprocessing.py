import os
import sys

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from data_processor import preprocess_slack_data

def get_data_path():
    """Get the path to the Slack data folder."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # Update path to include rtc_data subfolder
    return os.path.join(project_root, "JSON_processing/data", "rtc_data")

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