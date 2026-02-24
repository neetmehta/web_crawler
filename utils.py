import json
import os

def load_config(config_path="config.json"):
    """Loads and parses the JSON configuration file."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file '{config_path}' is missing.")
    
    with open(config_path, "r", encoding="utf-8") as file:
        return json.load(file)

def ensure_output_dir(file_path):
    """Creates the necessary directories for the output file if they don't exist."""
    directory = os.path.dirname(file_path)
    if directory:
        os.makedirs(directory, exist_ok=True)