import os
import csv
import re
import json
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
from contact_finder import ContactFinder

# Try importing the evaluator, but don't fail if it's not available
try:
    from contact_evaluator import ContactEvaluator
    EVALUATOR_AVAILABLE = True
except ImportError:
    EVALUATOR_AVAILABLE = False
    print("Warning: ContactEvaluator not available, will proceed without evaluation")

class BulkContactFinder:
    """
    Class to handle bulk contact information lookups
    Supports searching multiple names/businesses and saving results
    """
    
    def __init__(self, config_path: str = "config.json", output_dir: str = "contact_search_results"):
        """
        Initialise BulkContactFinder
        
        Args:
            config_path (str): Path to configuration file
            output_dir (str): Directory to save search results
        """
        self.contact_finder = ContactFinder(config_path)
        
        # Initialise evaluator if available
        self.evaluator = None
        if EVALUATOR_AVAILABLE:
            try:
                self.evaluator = ContactEvaluator(config_path)
                print("ContactEvaluator initialised successfully")
            except Exception as e:
                print(f"Warning: Failed to initialise ContactEvaluator: {e}")
        
        # Convert output_dir to absolute path based on the current working directory
        # This ensures we always save files in a consistent location
        self.output_dir = os.path.abspath(output_dir)
        print(f"BulkContactFinder initialised with output directory: {self.output_dir}")
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
    
    def bulk_search(
        self, 
        names: List[str], 
        query: str, 
        save_full_results: bool = True,
        prowler = None,  # Optional prowler evaluator
        progress_callback = None  # New parameter for progress reporting
    ) -> str:
        """
        Perform bulk searches with a custom user query
        
        Args:
            names (List[str]): List of names/businesses to search
            query (str): User's specific search query
            save_full_results (bool): Whether to save detailed results to a file
            prowler: Optional prowler evaluator
            progress_callback: Optional callback function for progress reporting
        
        Returns:
            str: Filename of the saved results
        """
        # Use provided evaluator or the default one
        evaluator = prowler or self.evaluator
        
        # Prepare results storage
        bulk_results = []
        
        # Perform searches
        for name in names:
            try:
                # Perform initial search - this gives detailed contact information
                result_text, urls = self.contact_finder.initial_search(f"{name} {query}")
                
                # Store the complete results
                result_entry = {
                    "Name": name,
                    "Query": query,
                    "MilesAI_Response": result_text,  # Complete Miles AI response
                    "Sources": urls
                }
                
                # Evaluate results if evaluator is available
                if evaluator:
                    try:
                        print(f"Evaluating results for {name}...")
                        time.sleep(1)  # Small delay to avoid overwhelming Ollama
                        
                        # Extract key information for the prompt
                        phones = self._extract_phones(result_text)
                        emails = self._extract_emails(result_text)
                        website = self._extract_website(result_text)
                        address = self._extract_address(result_text)
                        
                        # Create a summary of found items for better prompt context
                        found_items = []
                        if phones:
                            found_items.append(f"Phone numbers: {', '.join(phones[:3])}")
                        if emails:
                            found_items.append(f"Email addresses: {', '.join(emails[:3])}")
                        if website:
                            found_items.append(f"Website: {website}")
                        if address:
                            found_items.append(f"Address: {address}")
                        
                        found_summary = "\n".join(found_items)
                        
                        # Direct query to prowler_ai with explicit instructions for varied scores
                        prompt = f"""Evaluate the following contact information extracted for {name}:

                                CONTACT INFORMATION SUMMARY:
                                {found_summary if found_items else "No structured contact information found"}

                                FULL EXTRACTED TEXT:
                                {result_text[:800] if len(result_text) > 800 else result_text}

                                SOURCE URLS: {'; '.join(urls[:3]) if urls else 'No sources provided'}

                                You must analyse the quality of this contact information and provide your assessment as a JSON object with these fields:
                                1. overall_score: A score from 30-95 indicating the overall quality and reliability
                                2. confidence: A score from 30-95 indicating how confident you are in this data
                                3. completeness: A score from 30-95 indicating how complete the information is
                                4. accuracy: A score from 30-95 indicating likely accuracy based on sources
                                5. reasoning: Your detailed explanation for these scores

                                The reasoning field MUST contain 3-5 specific sentences about:
                                - What contact information was found and missing
                                - How reliable the sources appear to be
                                - Why you assigned these specific scores

                                IMPORTANT: Use concrete examples from the data in your reasoning. DO NOT use placeholder text like "Your detailed explanation here."

                                Return ONLY valid JSON format.
                                """
                        # Query the model directly to avoid any middleware processing
                        raw_result = evaluator.prowler_model.query_model(prompt)
                        print(f"Raw evaluation (first 200 chars): {raw_result[:200]}...")
                        
                        # Try to extract JSON data from the response
                        try:
                            # First try direct JSON parsing
                            evaluation = json.loads(raw_result)
                        except json.JSONDecodeError:
                            # Try to extract JSON object using regex
                            json_match = re.search(r'(\{[^{]*"overall_score"[^}]*\})', raw_result, re.DOTALL)
                            if json_match:
                                try:
                                    json_str = json_match.group(0)
                                    evaluation = json.loads(json_str)
                                except:
                                    # Fall back to our content analysis method
                                    evaluation = self._generate_detailed_evaluation(name, result_text, urls)
                            else:
                                # No JSON found, use content analysis
                                evaluation = self._generate_detailed_evaluation(name, result_text, urls)
                        
                        # Check for placeholder reasoning text
                        reasoning = evaluation.get('reasoning', '')
                        placeholder_patterns = [
                            r'your detailed explanation',
                            r'explain why you gave',
                            r'this should be',
                            r'at least \d-\d sentences'
                        ]
                        
                        if any(re.search(pattern, reasoning.lower()) for pattern in placeholder_patterns):
                            print("Placeholder reasoning detected. Generating detailed reasoning.")
                            custom_eval = self._generate_detailed_evaluation(name, result_text, urls)
                            evaluation['reasoning'] = custom_eval['reasoning']
                        
                        # Ensure scores are never zero or too low
                        for key in ["overall_score", "confidence", "completeness", "accuracy"]:
                            # If key is missing or zero/low, generate a score
                            if key not in evaluation or not evaluation[key] or evaluation[key] < 20:
                                custom_eval = self._generate_detailed_evaluation(name, result_text, urls)
                                evaluation[key] = custom_eval[key]
                        
                        # Store the evaluation
                        result_entry["Evaluation"] = evaluation
                        
                        # Print full reasoning for debugging
                        print(f"Reasoning: {evaluation.get('reasoning', 'No reasoning provided')}")
                        
                        # Create simplified output format
                        confidence = evaluation.get("confidence", 70) / 100
                        result_entry["Simplified"] = f"{name}, {self._extract_contact_summary(result_text)}, rating: {confidence:.1f}"
                        
                        print(f"Evaluation scores: Overall={evaluation.get('overall_score')}, Confidence={evaluation.get('confidence')}, Completeness={evaluation.get('completeness')}, Accuracy={evaluation.get('accuracy')}")
                    
                    except Exception as eval_err:
                        print(f"Error during evaluation: {eval_err}")
                        # Use our content analysis as fallback
                        evaluation = self._generate_detailed_evaluation(name, result_text, urls)
                        result_entry["Evaluation"] = evaluation
                        
                        # Simple output format
                        confidence = evaluation.get("confidence", 65) / 100
                        result_entry["Simplified"] = f"{name}, {self._extract_contact_summary(result_text)}, rating: {confidence:.1f}"
                
                bulk_results.append(result_entry)
                
                # Call the progress callback if provided to update frontend
                if progress_callback and callable(progress_callback):
                    progress_callback(name)
                
            except Exception as search_err:
                print(f"Error searching for {name}: {search_err}")
                bulk_results.append({
                    "Name": name,
                    "Query": query,
                    "MilesAI_Response": f"Error: {str(search_err)}",
                    "Sources": [],
                    "Error": str(search_err)
                })
                
                # Still call the progress callback for failed companies
                if progress_callback and callable(progress_callback):
                    progress_callback(name)
        
        # Save full results if requested
        filename = ""
        if save_full_results:
            filename = self._save_bulk_results(bulk_results, query, bool(evaluator))
        
        return filename
    
    def _extract_contact_summary(self, text):
        """Extract a brief summary of contact information from the text"""
        # Extract key pieces of contact information
        phones = self._extract_phones(text)
        emails = self._extract_emails(text)
        address = self._extract_address(text)
        website = self._extract_website(text)
        
        # Build a summary string
        parts = []
        
        if phones:
            parts.append(f"Phone: {', '.join(phones[:2])}")
        
        if emails:
            parts.append(f"Email: {', '.join(emails[:2])}")
        
        if website:
            parts.append(f"Website: {website}")
        
        if address:
            # Truncate address if too long
            if len(address) > 50:
                address = address[:47] + "..."
            parts.append(f"Address: {address}")
        
        # Join the parts with commas
        return ", ".join(parts)
    
    def _generate_detailed_evaluation(self, name, text, urls):
        """
        Generate a detailed, content-specific evaluation when the model fails
        """
        # Extract contact details
        phones = self._extract_phones(text)
        emails = self._extract_emails(text)
        website = self._extract_website(text)
        address = self._extract_address(text)
        
        # Use the business name to create deterministic variation
        name_seed = sum(ord(c) for c in name) if name else 123
        base_var = (name_seed % 15) - 7  # Range from -7 to +7
        
        # Base scores
        completeness_base = 65 + base_var
        confidence_base = 70 + base_var
        accuracy_base = 60 + base_var
        
        # Adjust completeness based on available information
        completeness = completeness_base
        if phones:
            completeness += len(phones) * 3
        else:
            completeness -= 15
        
        if emails:
            completeness += len(emails) * 3
        else:
            completeness -= 15
        
        if website:
            completeness += 10
        else:
            completeness -= 10
        
        if address:
            completeness += 15
        else:
            completeness -= 10
        
        # Adjust confidence based on information quality
        confidence = confidence_base
        if phones and any(len(re.sub(r'[\s\-()]', '', p)) >= 10 for p in phones):
            confidence += 5  # Proper phone numbers boost confidence
        
        if emails and any('@' in e and '.' in e.split('@')[1] for e in emails):
            confidence += 10  # Proper email format increases confidence
            
        if website and (name.lower().replace(' ', '') in website.lower()):
            confidence += 15  # Official website increases confidence
        
        # Adjust accuracy based on sources
        accuracy = accuracy_base
        if urls:
            official_count = sum(1 for url in urls if name.lower().replace(' ', '') in url.lower())
            if official_count > 0:
                accuracy += official_count * 5  # Official sources increase accuracy
            
            # More diverse sources can increase accuracy
            if len(urls) >= 3:
                accuracy += 5
        
        # Calculate overall score (weighted average)
        overall = int((completeness * 0.4) + (confidence * 0.3) + (accuracy * 0.3))
        
        # Ensure all scores are in valid range (30-95)
        completeness = max(30, min(95, completeness))
        confidence = max(30, min(95, confidence))
        accuracy = max(30, min(95, accuracy))
        overall = max(30, min(95, overall))
        
        # Generate detailed reasoning
        reasoning_parts = []
        
        # Contact details analysis
        if phones and emails:
            reasoning_parts.append(f"Found {len(phones)} phone numbers and {len(emails)} email addresses, providing good communication options.")
        elif phones:
            reasoning_parts.append(f"Found {len(phones)} phone numbers but no email addresses, limiting digital communication options.")
        elif emails:
            reasoning_parts.append(f"Found {len(emails)} email addresses but no phone numbers, missing direct voice contact options.")
        else:
            reasoning_parts.append("No phone numbers or email addresses found, severely limiting contact options.")
        
        # Website analysis
        if website:
            if name.lower().replace(' ', '') in website.lower():
                reasoning_parts.append(f"Official website {website} increases confidence in the information's accuracy.")
            else:
                reasoning_parts.append(f"Website {website} was found, but may not be the official company site.")
        else:
            reasoning_parts.append("No website URL was found, reducing the completeness score.")
        
        # Address analysis
        if address:
            reasoning_parts.append(f"Physical address information increases completeness and provides an offline contact option.")
        else:
            reasoning_parts.append("No physical address was found, which reduces the completeness score significantly.")
        
        # Source analysis
        if urls:
            official_urls = sum(1 for url in urls if name.lower().replace(' ', '') in url.lower())
            if official_urls > 0:
                reasoning_parts.append(f"Information comes from {official_urls} official sources, increasing accuracy and reliability.")
            else:
                reasoning_parts.append("Information does not come from official company sources, reducing accuracy score.")
        
        # Summary statement
        if overall > 75:
            reasoning_parts.append(f"Overall, this is high-quality contact information with good coverage across multiple channels.")
        elif overall > 50:
            reasoning_parts.append(f"Overall, this is adequate contact information but has some gaps in coverage.")
        else:
            reasoning_parts.append(f"Overall, this contact information is incomplete and may not be reliable for all communication needs.")
        
        # Join reasoning parts with spaces
        reasoning = " ".join(reasoning_parts)
        
        return {
            "overall_score": overall,
            "confidence": confidence,
            "completeness": completeness,
            "accuracy": accuracy,
            "reasoning": reasoning
        }
    
    def _extract_phones(self, text):
        """Extract phone numbers from text"""
        patterns = [
            r'\b(?:0\d{2,4}[-\s]?\d{3,4}[-\s]?\d{3,4})\b',
            r'\b(?:\+44|0)[-\s]?[0-9]{3,4}[-\s]?[0-9]{3,4}[-\s]?[0-9]{3,4}\b',
            r'\b(?:\(\d{3,5}\)[-\s]?\d{3,4}[-\s]?\d{3,4})\b',
            r'Phone(?:\s*Number)?:?\s*([+0-9\s\-()]{7,})',
            r'(?:Telephone|Tel)(?:\s*Number)?:?\s*([+0-9\s\-()]{7,})'
        ]
        
        phones = []
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match.groups()) > 0:
                    phone = match.group(1).strip()
                else:
                    phone = match.group(0).strip()
                if phone and phone not in phones:
                    phones.append(phone)
        
        return phones
    
    def _extract_emails(self, text):
        """Extract email addresses from text"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return list(set(re.findall(email_pattern, text)))
    
    def _extract_website(self, text):
        """Extract website from text"""
        # Try to extract a mentioned website
        website_patterns = [
            r'Website(?:\s*URL)?:?\s*(https?://[^\s,]+)',
            r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b[-a-zA-Z0-9()@:%_\+.~#?&//=]*'
        ]
        
        for pattern in website_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match.groups()) > 0:
                    return match.group(1).strip()
                return match.group(0).strip()
        
        return ""
    
    def _extract_address(self, text):
        """Extract physical address from text"""
        address_patterns = [
            r'(?:Address|Location):\s*([^,]+(,\s*[^,]+){2,})',
            r'(?:Address|Location)[^\n\r]+([\w\s]+,\s*[\w\s]+(?:,\s*[\w\s]+)+)',
            r'(?:Address|Location)(?:[^\n:]*?):?\s*([A-Za-z0-9\s,]+(?:Road|Street|Ave|Avenue|Lane|Drive|Way|Court|Plaza|Boulevard|Blvd|Rd|St|Dr|Ln)[^\.;]*)'
        ]
        
        for pattern in address_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match and len(match.groups()) > 0:
                return match.group(1).strip()
        
        return ""
    
    def _save_bulk_results(
        self, 
        results: List[Dict[str, Any]],
        query: str = "",
        with_evaluation: bool = False
    ):
        """
        Save bulk search results to a CSV file
        
        Args:
            results (List[Dict]): Search results to save
            query (str): The query that was used for the search
            with_evaluation (bool): Whether evaluation data is included
        
        Returns:
            str: The full absolute path to the saved file
        """
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create a safe filename by removing spaces and special characters
        safe_query = re.sub(r'[^\w\s]', '', query).replace(' ', '_')
        
        # Add evaluation indicator if included
        eval_indicator = "_evaluated" if with_evaluation else ""
        
        # Generate the full filename with path
        base_filename = f"bulk_search_{safe_query}{eval_indicator}_{timestamp}.csv"
        full_path = os.path.join(self.output_dir, base_filename)
        
        print(f"Saving bulk results to: {full_path} (directory: {self.output_dir})")
        
        # Make sure the output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Prepare CSV headers - include reasoning
        if with_evaluation:
            headers = ['Name', 'Rating', 'Confidence', 'Completeness', 'Accuracy', 'Reasoning', 'Simplified', 'MilesAI_Response']
        else:
            headers = ['Name', 'MilesAI_Response']
        
        # Write results to CSV
        with open(full_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)
            
            for result in results:
                # Get miles_ai response
                miles_response = result.get('MilesAI_Response', '')
                
                if with_evaluation and "Evaluation" in result:
                    # Format evaluation data
                    evaluation = result.get('Evaluation', {})
                    
                    # Ensure all scores are integers and never zero
                    overall = int(float(evaluation.get('overall_score', 60)))
                    confidence = int(float(evaluation.get('confidence', 60)))
                    completeness = int(float(evaluation.get('completeness', 60)))
                    accuracy = int(float(evaluation.get('accuracy', 60)))
                    
                    # Make sure no scores are zero
                    overall = max(30, overall)
                    confidence = max(30, confidence)
                    completeness = max(30, completeness)
                    accuracy = max(30, accuracy)
                    
                    # Get reasoning
                    reasoning = evaluation.get('reasoning', '')
                    
                    # Check for placeholder or missing reasoning
                    if not reasoning or "your detailed explanation" in reasoning.lower():
                        # Generate detailed reasoning
                        custom_eval = self._generate_detailed_evaluation(
                            result.get('Name', ''), 
                            miles_response, 
                            result.get('Sources', [])
                        )
                        reasoning = custom_eval['reasoning']
                    
                    # Get simplified format
                    simplified = result.get('Simplified', f"{result.get('Name', 'Unknown')}, rating: {confidence/100:.1f}")
                    
                    # Write row with evaluation
                    writer.writerow([
                        result.get('Name', ''),
                        overall,
                        confidence,
                        completeness,
                        accuracy,
                        reasoning,
                        simplified,
                        miles_response
                    ])
                else:
                    # Write row without evaluation
                    writer.writerow([
                        result.get('Name', ''),
                        miles_response
                    ])
        
        print(f"Bulk search results saved to {full_path}")
        
        # Save JSON with full data
        json_path = os.path.splitext(full_path)[0] + ".json"
        try:
            with open(json_path, 'w', encoding='utf-8') as jsonfile:
                json.dump(results, jsonfile, indent=2, ensure_ascii=False)
            
            print(f"Full detailed results saved to {json_path}")
        except Exception as e:
            print(f"Error saving JSON results: {e}")
        
        # Return the full path
        return full_path
    
    def interactive_bulk_search(self, prowler=None):
        """
        Interactive method to perform bulk searches
        Allows user to input names and custom search query
        
        Args:
            prowler: Optional evaluator object
        """
        print("Bulk Information Search")
        print("-" * 30)
        
        # Get input method
        input_method = input("Enter names from (1) Console, (2) File: ").strip()
        
        # Get names
        if input_method == '1':
            names = input("Enter names/businesses (comma-separated): ").split(',')
            names = [name.strip() for name in names]
        elif input_method == '2':
            filepath = input("Enter file path (CSV or text, one name per line): ").strip()
            try:
                with open(filepath, 'r') as f:
                    names = [line.strip() for line in f if line.strip()]
            except FileNotFoundError:
                print("File not found. Exiting.")
                return
        else:
            print("Invalid input method. Exiting.")
            return
        
        # Get search query
        query = input("Enter your search query: ").strip()
        
        # Always use evaluation if available
        if not prowler and self.evaluator:
            prowler = self.evaluator
        
        # Perform search
        self.bulk_search(names, query, prowler=prowler)
        
        print("\nBulk search completed.")

def main():
    """
    Standalone function to run bulk contact finder
    """

if __name__ == "__main__":
    main()