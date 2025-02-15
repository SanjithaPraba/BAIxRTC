from pathlib import Path
from data_processor import process_all_channels

def main():
    base_input_dir = Path("data/rtc_data")
    base_output_dir = Path("data/threads")
    
    process_all_channels(base_input_dir, base_output_dir)

if __name__ == "__main__":
    main() 