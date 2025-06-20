import yaml
import os
from pathlib import Path

def load_config():
    """
    Loads the configuration from config/config.yaml.
    The path is constructed relative to this script's location.
    """
    # Construct the path to the config file relative to the project root
    # __file__ -> src/core/config.py
    # os.path.dirname(__file__) -> src/core
    # os.path.dirname(os.path.dirname(os.path.dirname(__file__))) -> project root
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    config_path = os.path.join(project_root, 'config', 'config.yaml')
    
    try:
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        # A more robust error message
        print(f"Error: The configuration file was not found at {config_path}")
        print("Please ensure the config.yaml file exists in the 'config' directory at the project root.")
        return None
    except yaml.YAMLError as e:
        print(f"Error parsing the YAML configuration file: {e}")
        return None

# Load the configuration once when the module is imported
config = load_config()

def get_path(key, filename_key=None):
    """
    Constructs an absolute path from the config.
    
    Args:
        key (str): The key for the directory path in the config's 'data_paths'.
        filename_key (str, optional): The key for the filename in the config's 'file_names'.
        
    Returns:
        pathlib.Path: The absolute path.
    """
    project_root = Path(__file__).parent.parent
    base_path = project_root / config['data_paths'][key]
    
    if filename_key:
        return base_path / config['file_names'][filename_key]
    
    return base_path 