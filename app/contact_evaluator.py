import os
import json
import re
import time
from config_manager import ConfigManager
from model_manager import ModelManager

class ContactEvaluator:
    """
    Evaluates contact information extracted by miles_ai using prowler_ai
    """
    
    def __init__(self, config_path="config.json"):
        # Load the main config
        self.config = ConfigManager(config_path)
        
        # Create separate config for prowler
        self.prowler_config = ConfigManager("prowler_config.json")
        
        # Set default prowler config values if they don't exist
        if not self.prowler_config.get("model_name"):
            self.prowler_config.set("model_name", "prowler_ai")
            self.prowler_config.set("base_model", self.config.get("base_model", "qwen2.5:latest"))
            self.prowler_config.set("modelfile_path", "ProwlerModelfile")
            self.prowler_config.set("prompt_template_path", "prowler_prompt_template.txt")
        
        # Load the prompt template
        self._load_prompt_template()
        
        # Create model manager for prowler
        self.prowler_model = ModelManager(self.prowler_config)
    
    def _load_prompt_template(self):
        """
        Load the prompt template from the specified file
        """
        template_path = self.prowler_config.get("prompt_template_path", "prowler_prompt_template.txt")
        
        try:
            with open(template_path, 'r') as file:
                self.prompt_template = file.read().strip()
        except FileNotFoundError:
            raise FileNotFoundError(f"Prompt template file not found: {template_path}")
        except Exception as e:
            raise RuntimeError(f"Error reading prompt template: {e}")
    
    def setup(self):
        """Set up prowler model"""
        return self.prowler_model.create_model()
    
    def evaluate_contact_info(self, contact_info_text, business_name="", source_urls=None):
        """
        Evaluate contact info and return both detailed evaluation and simplified format
        
        Args:
            contact_info_text: Text output from miles_ai
            business_name: Name of the business
            source_urls: List of source URLs
            
        Returns:
            Dictionary with evaluation and simplified results
        """
        # Evaluate the contact information
        evaluation = self._evaluate_contact_info(contact_info_text, business_name, source_urls)
        
        # Format simplified output
        simplified = self._format_simplified_results(contact_info_text, evaluation)
        
        # Return both
        return {
            "evaluation": evaluation,
            "simplified": simplified,
            "contact_info": contact_info_text
        }
    
    def _evaluate_contact_info(self, contact_info_text, business_name="", source_urls=None):
        """
        Use prowler_ai to evaluate contact information
        """
        # Limit the size of the contact info text to avoid memory issues
        max_length = 800  # Set a reasonable character limit
        if len(contact_info_text) > max_length:
            contact_info_text = contact_info_text[:max_length] + "...[truncated]"
        
        # Prepare source URLs
        source_urls_text = ""
        if source_urls:
            if isinstance(source_urls, list):
                # Limit number of URLs to avoid large prompts
                limited_urls = source_urls[:3]  # Use only first 3 URLs
                source_urls_text = "\n".join(limited_urls)
            else:
                source_urls_text = str(source_urls)
        
        # Prepare the prompt by replacing placeholders
        prompt = self.prompt_template.replace('{{COMPANY_NAME}}', business_name or "Unknown Business")
        prompt = prompt.replace('{{CONTACT_INFO}}', contact_info_text)
        prompt = prompt.replace('{{SOURCE_URL}}', source_urls_text)
        
        print(f"Evaluating information for: {business_name}")
        
        try:
            # Query the prowler_ai model
            result = self.prowler_model.query_model(prompt)
            
            # Validate result is a non-empty string
            if not result or not isinstance(result, str):
                raise ValueError("Invalid response from prowler_ai: Empty or non-string response")
            
            # Try to parse the JSON
            try:
                evaluation = json.loads(result)
            except json.JSONDecodeError:
                # Try to extract JSON from the response
                json_match = re.search(r'(\{[^{]*"overall_score"[^}]*\})', result, re.DOTALL)
                
                if json_match:
                    json_str = json_match.group(0)
                    evaluation = json.loads(json_str)
                else:
                    # If JSON extraction fails, raise an error
                    raise ValueError(f"Cannot parse JSON from response: {result}")
            
            # Validate the evaluation dictionary
            required_keys = ["overall_score", "confidence", "completeness", "accuracy"]
            for key in required_keys:
                if key not in evaluation:
                    raise ValueError(f"Missing required key: {key}")
                
                # Ensure values are integers between 1-99
                try:
                    score = int(float(evaluation[key]))
                    if score < 1 or score > 99:
                        raise ValueError(f"Score {key} must be between 1-99")
                    evaluation[key] = score
                except (ValueError, TypeError):
                    raise ValueError(f"Invalid score for {key}")
            
            # Ensure reasoning is present
            if "reasoning" not in evaluation or not evaluation["reasoning"]:
                evaluation["reasoning"] = "Evaluation completed based on contact information."
            
            return evaluation
        
        except Exception as e:
            # Log the error
            print(f"Error in contact information evaluation: {str(e)}")
            
            # Raise the exception to allow caller to handle it
            raise

    def _format_simplified_results(self, contact_info_text, evaluation):
        """
        Format the results in a simplified format with confidence rating
        
        Args:
            contact_info_text: Text from miles_ai
            evaluation: Evaluation metrics dictionary
            
        Returns:
            String with simplified contact info and rating
        """
        # Extract key information from contact_info_text
        business_name = self._extract_business_name(contact_info_text)
        phone_numbers = self._extract_phone_numbers(contact_info_text)
        email_addresses = self._extract_email_addresses(contact_info_text)
        website_url = self._extract_website(contact_info_text)
        
        # Get confidence score (0-1 scale)
        confidence = evaluation.get("confidence", 50) / 100
        
        # Format the simplified output
        parts = []
        
        # Add business name
        parts.append(business_name)
        
        # Add phone numbers if available
        if phone_numbers:
            parts.append(f"Phone: {', '.join(phone_numbers)}")
        
        # Add email addresses if available
        if email_addresses:
            parts.append(f"Email: {', '.join(email_addresses)}")
        
        # Add website if available
        if website_url:
            parts.append(f"Website: {website_url}")
        
        # Add rating
        parts.append(f"rating: {confidence:.1f}")
        
        # Join all parts with comma separators
        result = ", ".join(parts)
        
        return result

    def _extract_business_name(self, text):
        """Extract business name from text"""
        # Try different patterns for business name
        patterns = [
            r"Business Name:\s*(.*?)(?:\n|$)",
            r"^(.*?)(?:Contact Information|\n)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # If no match, use the first line
        first_line = text.split('\n')[0].strip()
        if first_line:
            return first_line
            
        return "Unknown Business"

    def _extract_phone_numbers(self, text):
        """Extract phone numbers from text"""
        phone_numbers = []
        
        # Look for patterns like "Phone: 12345" or "Telephone: 12345"
        phone_pattern = r"(?:phone|telephone|tel|contact)[^\d]*([\d\s\-+.()]{7,})"
        matches = re.finditer(phone_pattern, text, re.IGNORECASE)
        for match in matches:
            phone = match.group(1).strip()
            if phone and phone not in phone_numbers:
                phone_numbers.append(phone)
        
        # Look for phone numbers in a structured format
        structured_pattern = r"(?:- |• )?(?:\*\*)?(?:Phone|Telephone|Tel)(?:\*\*)?: ?([\d\s\-+.()]{7,})"
        matches = re.finditer(structured_pattern, text, re.IGNORECASE)
        for match in matches:
            phone = match.group(1).strip()
            if phone and phone not in phone_numbers:
                phone_numbers.append(phone)
        
        # If still no match, look for anything that resembles a phone number
        if not phone_numbers:
            generic_pattern = r"\b(?:\+?[\d]{1,3}[-.\s]?)?(?:\([\d]{1,4}\)[-.\s]?)?[\d]{3,4}[-.\s]?[\d]{3,4}(?:[-.\s]?[\d]{1,4})?\b"
            matches = re.finditer(generic_pattern, text)
            for match in matches:
                phone = match.group(0).strip()
                if phone and phone not in phone_numbers:
                    phone_numbers.append(phone)
        
        return phone_numbers

    def _extract_email_addresses(self, text):
        """Extract email addresses from text"""
        # Find all email addresses in the text
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        
        # Filter out any duplicates
        return list(set(emails))

    def _extract_website(self, text):
        """Extract website URL from text"""
        # Look for website URL in the text
        website_patterns = [
            r"Website(?:\*\*)?:?\s*(https?://[^\s\n]+)",
            r"Website URL(?:\*\*)?:?\s*(https?://[^\s\n]+)",
            r"\b(https?://[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9]\.[a-zA-Z]{2,}(?:/[^\s\n]*)?)\b"
        ]
        
        for pattern in website_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return ""