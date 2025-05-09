import os
import openai
from typing import Dict, Any
from config_manager import ConfigManager

class OpenAIModelManager:
    """Manages OpenAI API interaction"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config = config_manager
        self.model_name = self.config.get("openai_model_name", "gpt-4")
        self.api_key = self.config.get("openai_api_key")
        self.system_prompt_path = self.config.get("system_prompt_path", "miles_system_prompt.txt")
        
        # Configure OpenAI client
        if self.api_key:
            # For newer OpenAI client
            self.client = openai.OpenAI(api_key=self.api_key)
        else:
            # Try to get from environment variable
            self.api_key = os.environ.get("OPENAI_API_KEY")
            if self.api_key:
                self.client = openai.OpenAI(api_key=self.api_key)
            else:
                print("Warning: No OpenAI API key found. Please set it in config or OPENAI_API_KEY environment variable")
                self.client = None
    
    def create_model(self) -> bool:
        """Validate OpenAI configuration - no need to create models with OpenAI"""
        if not self.api_key:
            print("Error: OpenAI API key not configured")
            return False
            
        print(f"OpenAI configuration validated. Using model: {self.model_name}")
        return True
    
    def query_model(self, prompt: str) -> str:
        """Query the OpenAI model"""
        if not self.client:
            return "Error: OpenAI API key not configured"
            
        try:
            system_prompt = self.load_system_prompt()
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error querying OpenAI: {str(e)}")
            return f"Error: {str(e)}"
            
    def load_system_prompt(self) -> str:
        """Load the system prompt from file"""
        try:
            with open(self.system_prompt_path, 'r') as file:
                return file.read()
        except Exception as e:
            print(f"Error loading system prompt: {str(e)}")
            return ""
            
    def load_prompt_template(self) -> str:
        """Load the prompt template from file - compatibility with ModelManager interface"""
        prompt_template_path = self.config.get("prompt_template_path", "prompt_template.txt")
        try:
            with open(prompt_template_path, 'r') as file:
                return file.read()
        except Exception as e:
            print(f"Error loading prompt template: {str(e)}")
            return ""