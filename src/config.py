import configparser
import os
from pathlib import Path

settings = {}

def load_config():
    """Finds and loads the config.ini file."""
    global settings
    
    base_path = Path(os.path.abspath(os.path.dirname(__file__)))
    config_path = base_path / "config.ini"
    
    print(f"🔍 Attempting to load configuration from: {config_path}")

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found at: {config_path}")

    config = configparser.ConfigParser()
    config.read(config_path)

    try:
        settings['employee_id'] = config.get('settings', 'employee_id')
        settings['backend_url'] = config.get('settings', 'backend_url')
        settings['daemon_api_key'] = config.get('settings', 'daemon_api_key')
        settings['idle_threshold_seconds'] = config.getint('settings', 'idle_threshold_seconds')
        print("✅ Configuration loaded successfully.")
    except (configparser.NoSectionError, configparser.NoOptionError) as e:
        raise ValueError(f"Missing required setting in config.ini: {e}")