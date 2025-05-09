from prowler_evaluator import ProwlerEvaluator
from openai_evaluator import OpenAIEvaluator
from config_manager import ConfigManager

def get_evaluator(config_manager: ConfigManager):
    """Factory function to get the appropriate evaluator based on configuration"""
    
    provider = config_manager.get("evaluator_provider", "prowler").lower()
    
    if provider == "openai":
        return OpenAIEvaluator(config_manager)
    elif provider == "prowler" or provider == "ollama":
        # Use ProwlerEvaluator for both prowler and ollama providers
        return ProwlerEvaluator(config_manager)
    else:
        print(f"Warning: Unknown evaluator provider '{provider}', defaulting to Prowler")
        return ProwlerEvaluator(config_manager)