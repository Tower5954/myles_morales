from model_manager import ModelManager
from openai_model_manager import OpenAIModelManager
from config_manager import ConfigManager

def get_model_manager(config_manager: ConfigManager):
    """Factory function to get the appropriate model manager based on configuration"""
    
    provider = config_manager.get("model_provider", "ollama").lower()
    
    if provider == "openai":
        return OpenAIModelManager(config_manager)
    elif provider == "ollama":
        return ModelManager(config_manager)
    else:
        print(f"Warning: Unknown model provider '{provider}', defaulting to Ollama")
        return ModelManager(config_manager)