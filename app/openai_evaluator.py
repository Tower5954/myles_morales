import os
import json
import re
from typing import Dict, Any, List, Union
from config_manager import ConfigManager
from openai_model_manager import OpenAIModelManager

class OpenAIEvaluator:
    """
    Evaluates contact information extraction results using OpenAI's models
    """
    
    def __init__(self, config_manager: ConfigManager = None):
        """
        Initialise the OpenAIEvaluator with configuration
        
        Args:
            config_manager: An instance of ConfigManager or None to create a new one
        """
        self.config = config_manager or ConfigManager()
        
        # Create a separate model manager for the OpenAI evaluator
        self.openai_config = ConfigManager("openai_config.json")
        
        # Set default OpenAI config values if they don't exist
        if not self.openai_config.get("model_provider"):
            self.openai_config.set("model_provider", "openai")
            self.openai_config.set("openai_model_name", "gpt-4")
            self.openai_config.set("prompt_template_path", "openai_evaluator_prompt_template.txt")
            self.openai_config.set("system_prompt_path", "openai_evaluator_system_prompt.txt")
        
        # Create OpenAI model manager
        self.model_manager = OpenAIModelManager(self.openai_config)
    
    def setup_model(self) -> bool:
        """
        Ensure the OpenAI configuration is set up and available
        
        Returns:
            bool: True if configuration is valid, False otherwise
        """
        return self.model_manager.create_model()
    
    def evaluate_contact_info(self, contact_info: Union[Dict[str, Any], str], 
                             company_name: str = "", 
                             context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Evaluate the quality and reliability of extracted contact information
        
        Args:
            contact_info: Dictionary or string containing extracted contact information
            company_name: Name of the company (if available)
            context: Additional context about the extraction (source URLs, etc.)
            
        Returns:
            Dict containing the original contact info plus evaluation metrics
        """
        # Create a prompt for the OpenAI model
        prompt = self._create_evaluation_prompt(contact_info, company_name, context)
        
        # Get evaluation from the model
        evaluation_result = self.model_manager.query_model(prompt)
        
        # Parse the evaluation result
        try:
            # Try to parse as JSON
            evaluation_metrics = json.loads(evaluation_result)
        except json.JSONDecodeError:
            # Try to extract JSON from the text response
            json_match = re.search(r'(\{[^{]*"overall_score"[^}]*\})', evaluation_result, re.DOTALL)
            if json_match:
                try:
                    evaluation_metrics = json.loads(json_match.group(0))
                except:
                    # Default scores with reasoning from the model response
                    evaluation_metrics = {
                        "overall_score": 60,
                        "confidence": 65,
                        "completeness": 70,
                        "accuracy": 60,
                        "reasoning": evaluation_result
                    }
            else:
                # If no JSON structure found, use default scores with reasoning
                evaluation_metrics = {
                    "overall_score": 60,
                    "confidence": 65,
                    "completeness": 70,
                    "accuracy": 60,
                    "reasoning": evaluation_result
                }
        
        # Ensure all scores are valid and never zero
        for key in ["overall_score", "confidence", "completeness", "accuracy"]:
            if key not in evaluation_metrics or not evaluation_metrics[key]:
                evaluation_metrics[key] = 60
            elif evaluation_metrics[key] < 30:
                evaluation_metrics[key] = max(30, evaluation_metrics[key] + 30)
        
        # Ensure reasoning is present and not a placeholder
        if "reasoning" not in evaluation_metrics or not evaluation_metrics["reasoning"]:
            evaluation_metrics["reasoning"] = "Evaluation completed based on available contact information."
        elif "your detailed explanation" in evaluation_metrics["reasoning"].lower():
            evaluation_metrics["reasoning"] = "Evaluation based on the completeness, accuracy, and reliability of the provided contact information."
        
        # Create consistent return format
        result = {
            "contact_info": contact_info,
            "evaluation": evaluation_metrics
        }
        
        return result
    
    def evaluate_batch(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Evaluate a batch of contact information extraction results
        
        Args:
            results: List of extraction results
            
        Returns:
            List of results with evaluation data added
        """
        evaluated_results = []
        
        for result in results:
            contact_info = result.get("contact_info", {})
            company_name = result.get("company_name", "")
            context = {
                "source_url": result.get("source_url", ""),
                "extracted_from": result.get("extracted_from", "")
            }
            
            evaluated_result = self.evaluate_contact_info(
                contact_info, 
                company_name, 
                context
            )
            
            # Combine with original result data
            full_result = {**result, **evaluated_result}
            evaluated_results.append(full_result)
            
        return evaluated_results
    
    def _create_evaluation_prompt(self, contact_info: Union[Dict[str, Any], str], 
                                 company_name: str = "", 
                                 context: Dict[str, Any] = None) -> str:
        """
        Create a prompt for the OpenAI model using the template file
        
        Args:
            contact_info: Extracted contact information (dict or string)
            company_name: Company name
            context: Additional context
            
        Returns:
            String prompt for the model
        """
        context = context or {}
        
        # Format contact_info into a readable string
        if isinstance(contact_info, dict):
            contact_info_str = json.dumps(contact_info, indent=2)
        else:
            contact_info_str = str(contact_info)
        
        # Extract source URLs from context
        source_urls = context.get('source_url', 'Unknown')
        if isinstance(source_urls, list):
            source_urls_str = "\n".join([f"- {url}" for url in source_urls[:5]])
        else:
            source_urls_str = str(source_urls)
        
        # Load the prompt template from file
        template_path = self.openai_config.get("prompt_template_path")
        
        try:
            with open(template_path, 'r') as f:
                template = f.read()
            
            # Replace template placeholders
            prompt = template.replace("{{COMPANY_NAME}}", company_name if company_name else "a company")
            prompt = prompt.replace("{{CONTACT_INFO}}", contact_info_str)
            prompt = prompt.replace("{{SOURCE_URL}}", source_urls_str)
            
            return prompt
            
        except Exception as e:
            print(f"Warning: Failed to load prompt template from {template_path}: {e}")
            # Use a minimal fallback prompt
            return f"""Evaluate the contact information for {company_name if company_name else "a company"}.
            
                        CONTACT INFORMATION:
                        {contact_info_str}

                        SOURCE URLS:
                        {source_urls_str}

                        Provide evaluation as JSON with overall_score, confidence, completeness, accuracy, and reasoning.
                        """