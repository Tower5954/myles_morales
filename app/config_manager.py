import os
import json
from typing import Dict, Any, Optional

class ConfigManager:
    """Manages configuration settings for the ContactFinder application"""
    
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print(f"Error: Config file {self.config_path} is not valid JSON. Using defaults.")
                return self._create_default_config()
        else:
            return self._create_default_config()
    
    def _create_default_config(self) -> Dict[str, Any]:
        """Create default configuration"""
        default_config = {
            "model_name": "miles_web",
            "base_model": "qwen2.5:latest", 
            "modelfile_path": "Modelfile",
            "prompt_template_path": "prompt_template.txt",
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "request_timeout": 10,
            "request_delay": 1.0,
            "max_search_results": 5,
            "max_depth": 2,
            "search_engine": "https://www.google.com/search?q=",
            "verbose": True
        }
        
        # Save default config
        self.save_config(default_config)
        return default_config
    
    def save_config(self, config: Dict[str, Any] = None) -> None:
        """Save configuration to file"""
        if config is None:
            config = self.config
        
        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=4)
    
    def get(self, key: str, default=None) -> Any:
        """Get a configuration value"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value"""
        self.config[key] = value
        self.save_config()