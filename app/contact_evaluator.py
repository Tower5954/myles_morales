import os
import json
import re
from evaluator_factory import get_evaluator
from config_manager import ConfigManager
from model_factory import get_model_manager  # You'll need to create this

class ContactEvaluator:
    """
    Evaluates contact information extracted by miles_ai using configurable evaluator
    """
    
    def __init__(self, config_path="config.json"):
        # Load the main config
        self.config_manager = ConfigManager(config_path)
        
        # Get the model provider from config (default to "ollama")
        model_provider = self.config_manager.get("model_provider", "ollama")
        evaluator_provider = self.config_manager.get("evaluator_provider", "prowler")
        
        print(f"Using model provider: {model_provider}")
        print(f"Using evaluator provider: {evaluator_provider}")
        
        # Get the appropriate evaluator using the factory
        self.evaluator = get_evaluator(self.config_manager)
        
        # Load the prompt template (still needed for some operations)
        self._load_prompt_template()
    
    def _load_prompt_template(self):
        """
        Load the prompt template from the specified file
        """
        # Determine template path based on evaluator provider
        evaluator_provider = self.config_manager.get("evaluator_provider", "prowler").lower()
        
        if evaluator_provider == "openai":
            template_path = self.config_manager.get("miles_prompt_template_path", "miles_prompt_template.txt")
        else:
            template_path = self.config_manager.get("prowler_prompt_template_path", "prowler_prompt_template.txt")
        
        try:
            with open(template_path, 'r') as file:
                self.prompt_template = file.read().strip()
        except FileNotFoundError:
            raise FileNotFoundError(f"Prompt template file not found: {template_path}")
        except Exception as e:
            raise RuntimeError(f"Error reading prompt template: {e}")
    
    def setup(self):
        """Set up the evaluator model"""
        return self.evaluator.setup_model()
    
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
        # Use the evaluator to evaluate the contact information
        context = {"source_url": source_urls} if source_urls else {}
        evaluation = self.evaluator.evaluate_contact_info(contact_info_text, business_name, context)
        
        # Extract the actual evaluation metrics
        if isinstance(evaluation, dict) and "evaluation" in evaluation:
            eval_metrics = evaluation["evaluation"]
        else:
            eval_metrics = evaluation
        
        # Format simplified output
        simplified = self._format_simplified_results(contact_info_text, eval_metrics)
        
        # Return both
        return {
            "evaluation": eval_metrics,
            "simplified": simplified,
            "contact_info": contact_info_text
        }
    
    def find_and_evaluate_contacts(self, business_name, urls=None):
        """
        Find and evaluate contact information for a business
        
        Args:
            business_name: Name of the business to search for
            urls: Optional list of URLs to scrape
            
        Returns:
            String with the evaluation results
        """
        # Import here to avoid circular imports
        from contact_finder import ContactFinder
        
        # Create a contact finder instance
        finder = ContactFinder(self.config_manager.config_path)
        
        # Find contact information
        if urls and len(urls) > 0:
            # Scrape the specified URL
            contact_info = finder.deep_scrape_url(urls[0], business_name)
            source_urls = urls
        else:
            # Do an initial search
            contact_info, found_urls = finder.initial_search(business_name)
            source_urls = found_urls
        
        # Evaluate the contact information
        result = self.evaluate_contact_info(contact_info, business_name, source_urls)
        
        # Save the result to a file
        os.makedirs("contact_search_results", exist_ok=True)
        safe_name = business_name.replace(" ", "_").replace("/", "_").replace("\\", "_")
        result_path = f"contact_search_results/{safe_name}_results.json"
        
        with open(result_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        # Format a summary of the result
        return self._format_result_summary(result, business_name)
    
    def _format_result_summary(self, result, business_name):
        """Format a summary of the evaluation result"""
        evaluation = result["evaluation"]
        simplified = result["simplified"]
        
        summary = [
            f"Contact Information Evaluation for {business_name}",
            "-" * 80,
            f"Overall Score: {evaluation.get('overall_score', 'N/A')}/100",
            f"Confidence: {evaluation.get('confidence', 'N/A')}/100",
            f"Completeness: {evaluation.get('completeness', 'N/A')}/100",
            f"Accuracy: {evaluation.get('accuracy', 'N/A')}/100",
            "",
            "Summary:",
            simplified,
            "",
            "Reasoning:",
            evaluation.get('reasoning', 'No reasoning provided.')
        ]
        
        return "\n".join(summary)
    @property
    def prowler_model(self):
        """Backward compatibility property for legacy code"""
        return self.evaluator.model_manager
    
    # Keep existing helper methods for extracting information
    def _format_simplified_results(self, contact_info_text, evaluation):
        """Format the results in a simplified format with confidence rating"""
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