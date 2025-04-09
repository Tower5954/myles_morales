import os
import ollama
from typing import Dict, Any
from config_manager import ConfigManager

class ModelManager:
    """Manages the Ollama model creation and interaction"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config = config_manager
        self.model_name = self.config.get("model_name")
        self.modelfile_path = self.config.get("modelfile_path")
        self.prompt_template_path = self.config.get("prompt_template_path")
        self.system_prompt_path = self.config.get("system_prompt_path")
        
        # Set default paths if not specified in config
        if not self.modelfile_path:
            self.modelfile_path = "Modelfile" if self.model_name == "miles_ai" else "ProwlerModelfile"
        
        if not self.prompt_template_path:
            self.prompt_template_path = "prompt_template.txt" if self.model_name == "miles_ai" else "prowler_prompt_template.txt"
            
        if not self.system_prompt_path:
            self.system_prompt_path = "miles_system_prompt.txt" if self.model_name == "miles_ai" else "prowler_system_prompt.txt"
    
    def create_model(self) -> bool:
        """Create the custom Ollama model"""
        print(f"Creating custom model: {self.model_name}")
        
        # Check if required files exist
        if not os.path.exists(self.modelfile_path):
            print(f"Error: Modelfile not found at {self.modelfile_path}")
            return False
            
        if not os.path.exists(self.prompt_template_path):
            print(f"Error: Prompt template not found at {self.prompt_template_path}")
            return False
            
        if not os.path.exists(self.system_prompt_path):
            print(f"Error: System prompt not found at {self.system_prompt_path}")
            return False
        
        # Check if the model already exists
        try:
            ollama.show(self.model_name)
            print(f"Model {self.model_name} already exists. Do you want to recreate it? (y/n)")
            choice = input().lower()
            if choice != 'y':
                print(f"Using existing model {self.model_name}")
                return True
            else:
                # Delete existing model
                os.system(f"ollama rm {self.model_name}")
                print(f"Removed existing model {self.model_name}")
        except:
            # Model doesn't exist, continue with creation
            pass
        
        # Create the model using Ollama CLI
        print(f"Creating model {self.model_name} from {self.modelfile_path}...")
        result = os.system(f"ollama create {self.model_name} -f {self.modelfile_path}")
        
        if result == 0:
            print(f"Model {self.model_name} created successfully")
            
            # Verify the model exists
            try:
                model_info = ollama.show(self.model_name)
                print(f"Model details: {model_info['license']} - {model_info['size']}")
                return True
            except Exception as e:
                print(f"Model created but verification failed: {str(e)}")
                return True
        else:
            print(f"Error: Failed to create model {self.model_name}")
            return False
    
    def query_model(self, prompt: str) -> str:
        """Query the Ollama model"""
        try:
            response = ollama.generate(
                model=self.model_name,
                prompt=prompt
            )
            return response['response']
        except Exception as e:
            print(f"Error querying model: {str(e)}")
            return f"Error: {str(e)}"
            
    def load_prompt_template(self) -> str:
        """Load the prompt template from file"""
        try:
            with open(self.prompt_template_path, 'r') as file:
                return file.read()
        except Exception as e:
            print(f"Error loading prompt template: {str(e)}")
            return ""
            
    def load_system_prompt(self) -> str:
        """Load the system prompt from file"""
        try:
            with open(self.system_prompt_path, 'r') as file:
                return file.read()
        except Exception as e:
            print(f"Error loading system prompt: {str(e)}")
            return ""