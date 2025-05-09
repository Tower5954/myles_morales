# import os
# import csv
# import re
# import json
# import time
# from typing import List, Dict, Any, Optional
# from datetime import datetime
# from contact_finder import ContactFinder

# # Try importing the evaluator, but don't fail if it's not available
# try:
#     from contact_evaluator import ContactEvaluator
#     EVALUATOR_AVAILABLE = True
# except ImportError:
#     EVALUATOR_AVAILABLE = False
#     print("Warning: ContactEvaluator not available, will proceed without evaluation")

# class BulkContactFinder:
#     """
#     Class to handle bulk contact information lookups
#     Supports searching multiple names/businesses and saving results
#     """
    
#     def __init__(self, config_path: str = "config.json", output_dir: str = "contact_search_results"):
#         """
#         Initialise BulkContactFinder
        
#         Args:
#             config_path (str): Path to configuration file
#             output_dir (str): Directory to save search results
#         """
#         self.contact_finder = ContactFinder(config_path)
        
#         # Initialise evaluator if available
#         self.evaluator = None
#         if EVALUATOR_AVAILABLE:
#             try:
#                 self.evaluator = ContactEvaluator(config_path)
#                 print("ContactEvaluator initialised successfully")
#             except Exception as e:
#                 print(f"Warning: Failed to initialise ContactEvaluator: {e}")
        
#         # Convert output_dir to absolute path based on the current working directory
#         # This ensures we always save files in a consistent location
#         self.output_dir = os.path.abspath(output_dir)
#         print(f"BulkContactFinder initialised with output directory: {self.output_dir}")
        
#         # Create output directory if it doesn't exist
#         os.makedirs(self.output_dir, exist_ok=True)
    
#     def bulk_search(
#         self, 
#         names: List[str], 
#         query: str, 
#         save_full_results: bool = True,
#         prowler = None,  # Optional prowler evaluator
#         progress_callback = None  # New parameter for progress reporting
#     ) -> str:
#         """
#         Perform bulk searches with a custom user query
        
#         Args:
#             names (List[str]): List of names/businesses to search
#             query (str): User's specific search query
#             save_full_results (bool): Whether to save detailed results to a file
#             prowler: Optional prowler evaluator
#             progress_callback: Optional callback function for progress reporting
        
#         Returns:
#             str: Filename of the saved results
#         """
#         # Use provided evaluator or the default one
#         evaluator = prowler or self.evaluator
        
#         # Prepare results storage
#         bulk_results = []
        
#         # Perform searches
#         for name in names:
#             try:
#                 print(f"Searching for contact information for: {name} {query}")
                
#                 # Initialize selenium scraper
#                 print("Initialising Selenium scraper...")
#                 from selenium_scraper import SeleniumScraper
#                 scraper = SeleniumScraper(headless=True)
                
#                 # Search for relevant URLs
#                 search_query = f"{name} {query}"
#                 urls = scraper.search(search_query)
#                 print(f"Found {len(urls)} search results")
                
#                 # Look for contact pages specifically
#                 contact_urls = []
#                 for url in urls:
#                     # Prioritize contact-us pages
#                     if 'contact' in url.lower():
#                         contact_urls.insert(0, url)
#                     else:
#                         contact_urls.append(url)
                
#                 # Make sure we have at least some URLs
#                 if not contact_urls:
#                     contact_urls = urls
                
#                 # Initialize results
#                 result_text = ""
#                 scraped_contents = []
                
#                 # Visit and scrape each URL (especially contact pages)
#                 print("Scraping contact pages for detailed information...")
#                 for url in contact_urls[:3]:  # Limit to first 3 URLs to avoid too much scraping
#                     print(f"Scraping URL: {url}")
#                     page_result = scraper.scrape_url(url)
                    
#                     if page_result and 'content' in page_result and page_result['content']:
#                         # Add the page content to our results
#                         scraped_contents.append(f"URL: {url}\n{page_result['content']}")
                
#                 # Close the scraper when done
#                 scraper.close()
#                 print("Browser closed")
                
#                 # Combine all scraped content
#                 if scraped_contents:
#                     result_text = "\n\n---\n\n".join(scraped_contents)
#                 else:
#                     result_text = "No content could be extracted from the URLs."
                
#                 # Store the complete results
#                 result_entry = {
#                     "Name": name,
#                     "Query": query,
#                     "MilesAI_Response": result_text,  # Complete content from all pages
#                     "Sources": contact_urls
#                 }
                
#                 # First try LLM-based extraction
#                 contact_info = self._extract_contact_info_with_llm(name, result_text, contact_urls)
                
#                 # Also extract directly with regex as backup/enhancement
#                 direct_info = self._extract_contact_info_direct(result_text)
                
#                 # Combine the results, preferring direct extraction for structured data
#                 combined_info = {
#                     "business_name": contact_info.get("business_name", name),
#                     "phones": direct_info.get("phones") or contact_info.get("phones") or [],
#                     "emails": direct_info.get("emails") or contact_info.get("emails") or [],
#                     "website": contact_info.get("website") or direct_info.get("website") or "",
#                     "address": direct_info.get("address") or contact_info.get("address") or ""
#                 }
                
#                 # Store the enhanced results
#                 result_entry["Contact_Info"] = combined_info
                
#                 # Evaluate results if evaluator is available
#                 if evaluator:
#                     try:
#                         print(f"Evaluating results for {name}...")
#                         time.sleep(1)  # Small delay to avoid overwhelming Ollama
                        
#                         # Use the enhanced contact info for evaluation
#                         phones = combined_info.get("phones", [])
#                         emails = combined_info.get("emails", [])
#                         website = combined_info.get("website", "")
#                         address = combined_info.get("address", "")
                        
#                         # Create a summary of found items for better prompt context
#                         found_items = []
#                         if phones:
#                             found_items.append(f"Phone numbers: {', '.join(phones[:3])}")
#                         if emails:
#                             found_items.append(f"Email addresses: {', '.join(emails[:3])}")
#                         if website:
#                             found_items.append(f"Website: {website}")
#                         if address:
#                             found_items.append(f"Address: {address}")
                        
#                         found_summary = "\n".join(found_items)
                        
#                         # Direct query to prowler_ai with explicit instructions for varied scores
#                         prompt = f"""Evaluate the following contact information extracted for {name}:

#                                 CONTACT INFORMATION SUMMARY:
#                                 {found_summary if found_items else "No structured contact information found"}

#                                 FULL EXTRACTED TEXT:
#                                 {result_text[:800] if len(result_text) > 800 else result_text}

#                                 SOURCE URLS: {'; '.join(contact_urls[:3]) if contact_urls else 'No sources provided'}

#                                 You must analyse the quality of this contact information and provide your assessment as a JSON object with these fields:
#                                 1. overall_score: A score from 30-95 indicating the overall quality and reliability
#                                 2. confidence: A score from 30-95 indicating how confident you are in this data
#                                 3. completeness: A score from 30-95 indicating how complete the information is
#                                 4. accuracy: A score from 30-95 indicating likely accuracy based on sources
#                                 5. reasoning: Your detailed explanation for these scores

#                                 The reasoning field MUST contain 3-5 specific sentences about:
#                                 - What contact information was found and missing
#                                 - How reliable the sources appear to be
#                                 - Why you assigned these specific scores

#                                 IMPORTANT: Use concrete examples from the data in your reasoning. DO NOT use placeholder text like "Your detailed explanation here."

#                                 Return ONLY valid JSON format.
#                                 """
#                         # Query the model directly to avoid any middleware processing
#                         raw_result = evaluator.evaluator.model_manager.query_model(prompt)
#                         print(f"Raw evaluation (first 200 chars): {raw_result[:200]}...")
                        
#                         # Try to extract JSON data from the response
#                         try:
#                             # First try direct JSON parsing
#                             evaluation = json.loads(raw_result)
#                         except json.JSONDecodeError:
#                             # Try to extract JSON object using regex
#                             json_match = re.search(r'(\{[^{]*"overall_score"[^}]*\})', raw_result, re.DOTALL)
#                             if json_match:
#                                 try:
#                                     json_str = json_match.group(0)
#                                     evaluation = json.loads(json_str)
#                                 except:
#                                     # Fall back to our content analysis method
#                                     evaluation = self._generate_detailed_evaluation(name, result_text, contact_urls)
#                             else:
#                                 # No JSON found, use content analysis
#                                 evaluation = self._generate_detailed_evaluation(name, result_text, contact_urls)
                        
#                         # Check for placeholder reasoning text
#                         reasoning = evaluation.get('reasoning', '')
#                         placeholder_patterns = [
#                             r'your detailed explanation',
#                             r'explain why you gave',
#                             r'this should be',
#                             r'at least \d-\d sentences'
#                         ]
                        
#                         if any(re.search(pattern, reasoning.lower()) for pattern in placeholder_patterns):
#                             print("Placeholder reasoning detected. Generating detailed reasoning.")
#                             custom_eval = self._generate_detailed_evaluation(name, result_text, contact_urls)
#                             evaluation['reasoning'] = custom_eval['reasoning']
                        
#                         # Ensure scores are never zero or too low
#                         for key in ["overall_score", "confidence", "completeness", "accuracy"]:
#                             # If key is missing or zero/low, generate a score
#                             if key not in evaluation or not evaluation[key] or evaluation[key] < 20:
#                                 custom_eval = self._generate_detailed_evaluation(name, result_text, contact_urls)
#                                 evaluation[key] = custom_eval[key]
                        
#                         # Store the evaluation
#                         result_entry["Evaluation"] = evaluation
                        
#                         # Print full reasoning for debugging
#                         print(f"Reasoning: {evaluation.get('reasoning', 'No reasoning provided')}")
                        
#                         # Create simplified output format using enhanced contact info
#                         phones_str = ', '.join(phones) if phones else ''
#                         emails_str = ', '.join(emails) if emails else ''
#                         contact_summary = f"Phone: {phones_str}, Email: {emails_str}, Website: {website}"
                        
#                         confidence = evaluation.get("confidence", 70) / 100
#                         result_entry["Simplified"] = f"{name}, {contact_summary}, rating: {confidence:.1f}"
                        
#                         print(f"Evaluation scores: Overall={evaluation.get('overall_score')}, Confidence={evaluation.get('confidence')}, Completeness={evaluation.get('completeness')}, Accuracy={evaluation.get('accuracy')}")
                    
#                     except Exception as eval_err:
#                         print(f"Error during evaluation: {eval_err}")
#                         # Use our content analysis as fallback
#                         evaluation = self._generate_detailed_evaluation(name, result_text, contact_urls)
#                         result_entry["Evaluation"] = evaluation
                        
#                         # Simple output format
#                         confidence = evaluation.get("confidence", 65) / 100
                        
#                         # Get contact info even when evaluation fails
#                         phones = combined_info.get("phones", [])
#                         emails = combined_info.get("emails", [])
#                         website = combined_info.get("website", "")
#                         phones_str = ', '.join(phones) if phones else ''
#                         emails_str = ', '.join(emails) if emails else ''
#                         contact_summary = f"Phone: {phones_str}, Email: {emails_str}, Website: {website}"
                        
#                         result_entry["Simplified"] = f"{name}, {contact_summary}, rating: {confidence:.1f}"
                
#                 bulk_results.append(result_entry)
                
#                 # Call the progress callback if provided
#                 if progress_callback and callable(progress_callback):
#                     progress_callback(name)
                
#             except Exception as search_err:
#                 print(f"Error searching for {name}: {search_err}")
#                 import traceback
#                 traceback.print_exc()
                
#                 bulk_results.append({
#                     "Name": name,
#                     "Query": query,
#                     "MilesAI_Response": f"Error: {str(search_err)}",
#                     "Sources": [],
#                     "Error": str(search_err)
#                 })
                
#                 # Still call the progress callback for failed companies
#                 if progress_callback and callable(progress_callback):
#                     progress_callback(name)
        
#         # Save full results if requested
#         filename = ""
#         if save_full_results:
#             filename = self._save_bulk_results(bulk_results, query, bool(evaluator))
        
#         return filename
    
#     def _extract_contact_info_with_llm(self, name, text, urls):
#         """
#         Use the LLM to extract structured contact information with context
        
#         Args:
#             name (str): Business name
#             text (str): Text to extract information from
#             urls (list): Source URLs
            
#         Returns:
#             dict: Structured contact information
#         """
#         # Create a prompt specifically for context-aware contact information extraction
#         prompt = f"""You are Miles AI, a specialized contact information extraction assistant.
        
#         TASK: Extract ALL contact information for "{name}" from the following text.
        
#         TEXT:
#         {text[:20000]}  # Limit to 20k chars to avoid token limits
        
#         SOURCE URLS: {'; '.join(urls[:3]) if urls else 'No sources provided'}
        
#         Extract and return ONLY the following information in JSON format:
#         {{
#             "business_name": "The most complete official name found",
#             "phones": [
#                 {{"number": "Phone number 1", "description": "Department or purpose of this phone number"}},
#                 {{"number": "Phone number 2", "description": "Department or purpose of this phone number"}}
#             ],
#             "emails": [
#                 {{"address": "Email address 1", "description": "Department or purpose of this email"}},
#                 {{"address": "Email address 2", "description": "Department or purpose of this email"}}
#             ],
#             "website": "Main website URL",
#             "address": "The primary physical address with postal code",
#             "additional_locations": [
#                 {{"name": "Location name", "address": "Full address", "phone": "Location phone number"}}
#             ]
#         }}
        
#         CRITICAL INSTRUCTIONS:
#         1. Search through the ENTIRE text and extract EVERY single phone number and email you can find
#         2. For each phone number, ALWAYS include what it's for (e.g., "Main Switchboard", "Appointments", "Ward 5", etc.)
#         3. For each email address, ALWAYS include what it's for (e.g., "General Inquiries", "Support", "Sales Team", etc.)
#         4. Include ALL department-specific numbers and emails with their proper labels
#         5. For healthcare organizations, make sure to include ALL ward, department, and service contact details
#         6. If there are multiple locations or branches, list them with their specific contact details
#         7. IMPORTANT: Ensure your response is valid, complete JSON with no truncation
#         8. For website, ONLY include the main domain (e.g., "https://example.com") without fragment identifiers or query parameters
        
#         Your goal is to create a COMPREHENSIVE and WELL-STRUCTURED contact directory with proper labels for all numbers and emails.
#         """
        
#         # Query the model via the evaluator or contact_finder
#         if hasattr(self.contact_finder, 'model_manager') and self.contact_finder.model_manager:
#             # Use the model manager if available
#             raw_result = self.contact_finder.model_manager.query_model(prompt)
#         elif self.evaluator and hasattr(self.evaluator, 'evaluator') and hasattr(self.evaluator.evaluator, 'model_manager'):
#             # Otherwise use the evaluator
#             raw_result = self.evaluator.evaluator.model_manager.query_model(prompt)
#         else:
#             # If no model access, return empty result
#             print("Warning: No model available for contact extraction")
#             return {
#                 "business_name": name,
#                 "phones": [],
#                 "emails": [],
#                 "website": "",
#                 "address": ""
#             }
        
#         # Check if we got a valid response
#         if not raw_result or len(raw_result.strip()) < 10:
#             print("Warning: Received empty or very short response from LLM")
#             # Prepare a minimal structure with the name
#             return {
#                 "business_name": name,
#                 "phones": [],
#                 "emails": [],
#                 "website": self._extract_clean_domain_from_urls(urls),
#                 "address": ""
#             }
        
#         # Try to parse the JSON response with improved robustness
#         contact_info = self._parse_llm_response(raw_result)
        
#         # If parsing failed completely, create a minimal structure
#         if not contact_info:
#             contact_info = {
#                 "business_name": name,
#                 "phones": [],
#                 "emails": [],
#                 "website": self._extract_clean_domain_from_urls(urls),
#                 "address": ""
#             }
        
#         # Clean the website URL if one was extracted
#         if contact_info.get("website"):
#             contact_info["website"] = self._clean_website_url(contact_info["website"])
#         elif urls:
#             # If no website was extracted but we have URLs, use the first URL's domain
#             contact_info["website"] = self._extract_clean_domain_from_urls(urls)
        
#         # Ensure business name is present
#         if not contact_info.get("business_name"):
#             contact_info["business_name"] = name
        
#         # Ensure other fields exist
#         if "phones" not in contact_info:
#             contact_info["phones"] = []
#         if "emails" not in contact_info:
#             contact_info["emails"] = []
#         if "address" not in contact_info:
#             contact_info["address"] = ""
#         if "additional_locations" not in contact_info:
#             contact_info["additional_locations"] = []
        
#         return contact_info

#     def _parse_llm_response(self, raw_text):
#         """
#         Robustly parse the LLM response to extract structured contact information.
#         Returns a dictionary with the extracted info or an empty dict if parsing fails.
#         """
#         try:
#             # Remove markdown code blocks if present
#             cleaned_text = raw_text.strip()
#             if "```json" in cleaned_text:
#                 cleaned_text = re.sub(r'```json\s+|\s+```', '', cleaned_text)
#             elif "```" in cleaned_text:
#                 cleaned_text = re.sub(r'```\s+|\s+```', '', cleaned_text)
            
#             # Add missing braces if needed
#             bracket_diff = cleaned_text.count('{') - cleaned_text.count('}')
#             if bracket_diff > 0:
#                 cleaned_text += '}' * bracket_diff
#                 print(f"Fixed unbalanced brackets by adding {bracket_diff} closing braces")
            
#             # Try to parse the cleaned JSON
#             try:
#                 contact_info = json.loads(cleaned_text)
#                 print("Successfully parsed contact info from JSON")
#                 return contact_info
#             except json.JSONDecodeError as e:
#                 print(f"JSON parsing error: {e}")
#                 pass
            
#             # Didn't work, look for JSON object using regex
#             json_match = re.search(r'(\{[^{]*"business_name"[^}]*\})', cleaned_text, re.DOTALL)
#             if json_match:
#                 try:
#                     json_str = json_match.group(0)
#                     # Try to add missing braces
#                     bracket_diff = json_str.count('{') - json_str.count('}')
#                     if bracket_diff > 0:
#                         json_str += '}' * bracket_diff
                    
#                     contact_info = json.loads(json_str)
#                     print("Extracted contact info via regex pattern")
#                     return contact_info
#                 except Exception as regex_err:
#                     print(f"Error parsing JSON extracted via regex: {regex_err}")
#                     pass
            
#             # JSON parsing failed, try direct extraction from text
#             print("Attempting direct extraction from LLM response...")
#             contact_info = {}
            
#             # Try to extract business name with regex
#             business_match = re.search(r'"business_name"\s*:\s*"([^"]+)', cleaned_text)
#             if business_match:
#                 contact_info["business_name"] = business_match.group(1).strip()
            
#             # Extract phone numbers with descriptions
#             phones = []
#             phone_matches = re.finditer(r'"number"\s*:\s*"([^"]+)', cleaned_text)
            
#             for match in phone_matches:
#                 phone = match.group(1).strip()
#                 context = cleaned_text[match.end():match.end()+100]  # Look ahead for description
                
#                 desc_match = re.search(r'"description"\s*:\s*"([^"]+)', context)
#                 desc = desc_match.group(1).strip() if desc_match else "Main"
                
#                 phones.append({"number": phone, "description": desc})
            
#             if phones:
#                 contact_info["phones"] = phones
            
#             # Extract emails with descriptions
#             emails = []
#             email_matches = re.finditer(r'"address"\s*:\s*"([^"]+@[^"]+)', cleaned_text)
            
#             for match in email_matches:
#                 email = match.group(1).strip()
#                 context = cleaned_text[match.end():match.end()+100]  # Look ahead for description
                
#                 desc_match = re.search(r'"description"\s*:\s*"([^"]+)', context)
#                 desc = desc_match.group(1).strip() if desc_match else "General"
                
#                 emails.append({"address": email, "description": desc})
            
#             if emails:
#                 contact_info["emails"] = emails
            
#             # Try to extract website 
#             website_match = re.search(r'"website"\s*:\s*"([^"]+)', cleaned_text)
#             if website_match:
#                 contact_info["website"] = website_match.group(1).strip()
            
#             # Try to extract address
#             address_match = re.search(r'"address"\s*:\s*"([^"]+)', cleaned_text)
#             if address_match:
#                 contact_info["address"] = address_match.group(1).strip()
            
#             # If we found any contact information, return it
#             if any(key in contact_info for key in ["business_name", "phones", "emails", "website", "address"]):
#                 print("Successfully extracted contact information via regex patterns")
#                 return contact_info
            
#         except Exception as e:
#             print(f"Unexpected error extracting contact info: {e}")
        
#         # Return empty dict if all extraction methods failed
#         return {}

#     def _extract_clean_domain_from_urls(self, urls):
#         """
#         Extract a clean domain from the provided URLs
#         """
#         if not urls or len(urls) == 0:
#             return ""
        
#         # Try each URL until we find one with a valid domain
#         for url in urls:
#             clean_url = self._clean_website_url(url)
#             if clean_url:
#                 return clean_url
        
#         return ""

#     def _clean_website_url(self, url):
#         """
#         Clean a website URL to just the main domain
#         """
#         if not url:
#             return ""
        
#         # Remove fragments and query params
#         clean_url = url.split('#')[0].split('?')[0]
        
#         # Extract just the domain
#         if '://' in clean_url:
#             try:
#                 domain_parts = clean_url.split('://')
#                 if len(domain_parts) > 1:
#                     protocol = domain_parts[0]
#                     domain = domain_parts[1].split('/')[0]
#                     return f"{protocol}://{domain}"
#             except Exception:
#                 pass
        
#         # If we couldn't extract a clean domain, return the URL as is
#         return url

#     def _extract_contact_info_direct(self, text):
#         """
#         Extract contact information directly from text using regex patterns,
#         with better cleanup of UI elements and language lists
#         """
#         # Clean the text before processing
#         # Remove Google Translate language lists
#         cleaned_text = text
        
#         # Remove common Google Translate language list sections
#         translate_patterns = [
#             r'Select Language[\s\S]+?(?:Powered by[\s\S]+?Translate|Rate this translation)',
#             r'(?:Abkhaz|Acehnese|Acholi)[\s\S]+?(?:Zulu|Zapotec|Yoruba)',  # List of languages
#             r'Text size:[\s\S]+?(?:Reset contrast|Reset text size)',  # Text size controls
#         ]
        
#         for pattern in translate_patterns:
#             cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.IGNORECASE)
        
#         # Extract business name from title or h1
#         business_name = ""
#         title_match = re.search(r'<title>([^|<]+)', cleaned_text)
#         if title_match:
#             title_text = title_match.group(1).strip()
#             if '|' in title_text:
#                 title_text = title_text.split('|')[0].strip()
#             if len(title_text) > 5 and len(title_text) < 100:  # Reasonable length for a business name
#                 business_name = title_text
        
#         # Extract emails
#         email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
#         email_matches = re.findall(email_pattern, cleaned_text)
        
#         # Format emails with descriptions
#         emails = []
#         for email in set(email_matches):  # Deduplicate
#             # Try to determine purpose from email
#             purpose = "General Enquiries"
            
#             if 'admin' in email.lower():
#                 purpose = "Administration"
#             elif 'info' in email.lower():
#                 purpose = "Information"
#             elif 'support' in email.lower():
#                 purpose = "Support"
#             elif 'contact' in email.lower():
#                 purpose = "Contact"
#             elif 'sales' in email.lower():
#                 purpose = "Sales"
#             elif 'help' in email.lower():
#                 purpose = "Help"
            
#             emails.append({"address": email, "description": purpose})
        
#         # Extract phone numbers - comprehensive UK patterns
#         phones = []
#         uk_patterns = [
#             # General UK formats
#             r'\+44\s?(?:\(0\))?\s?(?:\d[\d\s\-\(\)\.]{7,17}\d)',
#             r'0(?:1\d{3}|2\d{2}|3\d{2}|5\d{2}|7\d{3}|8\d{3})\s?[\d\s\-]{6,10}',
#             # Freephone/special numbers
#             r'(?<!\d)0800\s?\d{3}\s?\d{4}(?!\d)',
#             # Numbers with labels
#             r'(?:telephone|phone|tel|call|dial|mobile|switchboard|hotline)(?:\s*number)?(?:\s*:)?\s*([+0-9\s\-()\.]{7,})',
#         ]
        
#         # Track already processed phone numbers
#         processed_phones = set()
        
#         # Find all phone numbers
#         for pattern in uk_patterns:
#             matches = re.finditer(pattern, cleaned_text, re.IGNORECASE)
#             for match in matches:
#                 # If match is a tuple (from capturing group), get the relevant part
#                 phone = match.group(1) if len(match.groups()) > 0 else match.group(0)
#                 # Clean the phone number
#                 phone = re.sub(r'[^\d\+\s\-\(\)]', '', phone)
#                 phone = re.sub(r'\s+', ' ', phone).strip()
                
#                 # Skip if too short
#                 if not phone or len(re.sub(r'[\s\-\(\)\+]', '', phone)) < 6:
#                     continue
                    
#                 # Check for duplicates
#                 norm_phone = re.sub(r'[\s\-\(\)\+]', '', phone)
#                 if norm_phone in processed_phones:
#                     continue
                    
#                 processed_phones.add(norm_phone)
                
#                 # Get context to determine phone purpose
#                 start_pos = max(0, match.start() - 50)
#                 context = cleaned_text[start_pos:match.end() + 20]
                
#                 # Default purpose
#                 purpose = "Main"
                
#                 # Look for department labels
#                 dept_words = re.findall(r'(Ward|Unit|Department|Centre|Center|Team|PALS|Outpatients|Appointments|Switchboard|Hotline|Support|Enquiries|Emergency|Reception)', context, re.IGNORECASE)
                
#                 if dept_words:
#                     purpose = dept_words[-1].strip()
                
#                 phones.append({"number": phone, "description": purpose})
        
#         # Extract address using UK postcode pattern
#         postcode_pattern = r'[A-Z]{1,2}[0-9][0-9A-Z]?\s?[0-9][A-Z]{2}'
#         address = ""
        
#         postcode_matches = re.finditer(postcode_pattern, cleaned_text)
#         for match in postcode_matches:
#             # Get context around the postcode
#             start_pos = max(0, match.start() - 100)
#             end_pos = min(len(cleaned_text), match.end() + 50)
#             context = cleaned_text[start_pos:end_pos]
#             # Clean up and use as address
#             address = re.sub(r'\s+', ' ', context).strip()
#             break  # Just use the first good match
        
#         # Extract website - and just get the domain
#         website_pattern = r'https?://(?:www\.)?[a-zA-Z0-9][-a-zA-Z0-9.]{1,61}[a-zA-Z0-9]\.[a-zA-Z]{2,}(?:/[^\s]*)?'
#         website = ""
#         website_matches = re.findall(website_pattern, cleaned_text)
#         if website_matches:
#             raw_website = website_matches[0]
            
#             # Clean to just get domain
#             website = raw_website.split('#')[0].split('?')[0]
#             if '://' in website:
#                 parts = website.split('://')
#                 if len(parts) > 1:
#                     domain = parts[1].split('/')[0]
#                     website = f"{parts[0]}://{domain}"
        
#         return {
#             "business_name": business_name,
#             "phones": phones,
#             "emails": emails,
#             "website": website,
#             "address": address
#         }
    
#     def _extract_contact_info_direct(self, text):
#         """
#         Extract contact information directly from text using regex patterns,
#         with better cleanup of UI elements and language lists
#         """
#         # Clean the text before processing
#         # Remove Google Translate language lists
#         cleaned_text = text
        
#         # Remove common Google Translate language list sections
#         translate_patterns = [
#             r'Select Language[\s\S]+?(?:Powered by[\s\S]+?Translate|Rate this translation)',
#             r'(?:Abkhaz|Acehnese|Acholi)[\s\S]+?(?:Zulu|Zapotec|Yoruba)',  # List of languages
#             r'Text size:[\s\S]+?(?:Reset contrast|Reset text size)',  # Text size controls
#         ]
        
#         for pattern in translate_patterns:
#             cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.IGNORECASE)
        
#         # Extract emails
#         email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
#         emails = list(set(re.findall(email_pattern, cleaned_text)))
        
#         # Extract phone numbers - comprehensive UK patterns
#         phones = []
#         uk_patterns = [
#             # General UK formats
#             r'\+44\s?(?:\(0\))?\s?(?:\d[\d\s\-\(\)\.]{7,17}\d)',
#             r'0(?:1\d{3}|2\d{2}|3\d{2}|5\d{2}|7\d{3}|8\d{3})\s?[\d\s\-]{6,10}',
#             # Freephone/special numbers
#             r'(?<!\d)0800\s?\d{3}\s?\d{4}(?!\d)',
#             # Numbers with labels
#             r'(?:telephone|phone|tel|call|dial|mobile|switchboard|hotline)(?:\s*number)?(?:\s*:)?\s*([+0-9\s\-()\.]{7,})',
#         ]
        
#         # Find all phone numbers
#         for pattern in uk_patterns:
#             matches = re.findall(pattern, cleaned_text, re.IGNORECASE)
#             for match in matches:
#                 # If match is a tuple (from capturing group), get the relevant part
#                 phone = match[0] if isinstance(match, tuple) else match
#                 # Clean the phone number
#                 phone = re.sub(r'[^\d\+\s\-\(\)]', '', phone)
#                 phone = re.sub(r'\s+', ' ', phone).strip()
#                 # Add if not already found
#                 if phone and len(re.sub(r'[\s\-\(\)\+]', '', phone)) >= 6:
#                     phones.append(phone)
        
#         # Extract address using UK postcode pattern
#         postcode_pattern = r'[A-Z]{1,2}[0-9][0-9A-Z]?\s?[0-9][A-Z]{2}'
#         address = ""
        
#         postcode_matches = re.finditer(postcode_pattern, cleaned_text)
#         for match in postcode_matches:
#             # Get context around the postcode
#             start_pos = max(0, match.start() - 100)
#             end_pos = min(len(cleaned_text), match.end() + 50)
#             context = cleaned_text[start_pos:end_pos]
#             # Clean up and use as address
#             address = re.sub(r'\s+', ' ', context).strip()
#             break  # Just use the first good match
        
#         # Extract website
#         website_pattern = r'https?://(?:www\.)?[a-zA-Z0-9][-a-zA-Z0-9.]{1,61}[a-zA-Z0-9]\.[a-zA-Z]{2,}(?:/[^\s]*)?'
#         website = ""
#         website_matches = re.findall(website_pattern, cleaned_text)
#         if website_matches:
#             website = website_matches[0]
        
#         return {
#             "phones": list(set(phones)),
#             "emails": emails,
#             "website": website,
#             "address": address
#         }
    
#     def _extract_contact_summary(self, text):
#         """Extract a brief summary of contact information from the text"""
#         # Extract key pieces of contact information
#         phones = self._extract_phones(text)
#         emails = self._extract_emails(text)
#         address = self._extract_address(text)
#         website = self._extract_website(text)
        
#         # Build a summary string
#         parts = []
        
#         if phones:
#             parts.append(f"Phone: {', '.join(phones[:2])}")
        
#         if emails:
#             parts.append(f"Email: {', '.join(emails[:2])}")
        
#         if website:
#             parts.append(f"Website: {website}")
        
#         if address:
#             # Truncate address if too long
#             if len(address) > 50:
#                 address = address[:47] + "..."
#             parts.append(f"Address: {address}")
        
#         # Join the parts with commas
#         return ", ".join(parts)
    
#     def _generate_detailed_evaluation(self, name, text, urls):
#         """
#         Generate a detailed, content-specific evaluation when the model fails
#         """
#         # Extract contact details
#         phones = self._extract_phones(text)
#         emails = self._extract_emails(text)
#         website = self._extract_website(text)
#         address = self._extract_address(text)
        
#         # Use the business name to create deterministic variation
#         name_seed = sum(ord(c) for c in name) if name else 123
#         base_var = (name_seed % 15) - 7  # Range from -7 to +7
        
#         # Base scores
#         completeness_base = 65 + base_var
#         confidence_base = 70 + base_var
#         accuracy_base = 60 + base_var
        
#         # Adjust completeness based on available information
#         completeness = completeness_base
#         if phones:
#             completeness += len(phones) * 3
#         else:
#             completeness -= 15
        
#         if emails:
#             completeness += len(emails) * 3
#         else:
#             completeness -= 15
        
#         if website:
#             completeness += 10
#         else:
#             completeness -= 10
        
#         if address:
#             completeness += 15
#         else:
#             completeness -= 10
        
#         # Adjust confidence based on information quality
#         confidence = confidence_base
#         if phones and any(len(re.sub(r'[\s\-()]', '', p)) >= 10 for p in phones):
#             confidence += 5  # Proper phone numbers boost confidence
        
#         if emails and any('@' in e and '.' in e.split('@')[1] for e in emails):
#             confidence += 10  # Proper email format increases confidence
            
#         if website and (name.lower().replace(' ', '') in website.lower()):
#             confidence += 15  # Official website increases confidence
        
#         # Adjust accuracy based on sources
#         accuracy = accuracy_base
#         if urls:
#             official_count = sum(1 for url in urls if name.lower().replace(' ', '') in url.lower())
#             if official_count > 0:
#                 accuracy += official_count * 5  # Official sources increase accuracy
            
#             # More diverse sources can increase accuracy
#             if len(urls) >= 3:
#                 accuracy += 5
        
#         # Calculate overall score (weighted average)
#         overall = int((completeness * 0.4) + (confidence * 0.3) + (accuracy * 0.3))
        
#         # Ensure all scores are in valid range (30-95)
#         completeness = max(30, min(95, completeness))
#         confidence = max(30, min(95, confidence))
#         accuracy = max(30, min(95, accuracy))
#         overall = max(30, min(95, overall))
        
#         # Generate detailed reasoning
#         reasoning_parts = []
        
#         # Contact details analysis
#         if phones and emails:
#             reasoning_parts.append(f"Found {len(phones)} phone numbers and {len(emails)} email addresses, providing good communication options.")
#         elif phones:
#             reasoning_parts.append(f"Found {len(phones)} phone numbers but no email addresses, limiting digital communication options.")
#         elif emails:
#             reasoning_parts.append(f"Found {len(emails)} email addresses but no phone numbers, missing direct voice contact options.")
#         else:
#             reasoning_parts.append("No phone numbers or email addresses found, severely limiting contact options.")
        
#         # Website analysis
#         if website:
#             if name.lower().replace(' ', '') in website.lower():
#                 reasoning_parts.append(f"Official website {website} increases confidence in the information's accuracy.")
#             else:
#                 reasoning_parts.append(f"Website {website} was found, but may not be the official company site.")
#         else:
#             reasoning_parts.append("No website URL was found, reducing the completeness score.")
        
#         # Address analysis
#         if address:
#             reasoning_parts.append(f"Physical address information increases completeness and provides an offline contact option.")
#         else:
#             reasoning_parts.append("No physical address was found, which reduces the completeness score significantly.")
        
#         # Source analysis
#         if urls:
#             official_urls = sum(1 for url in urls if name.lower().replace(' ', '') in url.lower())
#             if official_urls > 0:
#                 reasoning_parts.append(f"Information comes from {official_urls} official sources, increasing accuracy and reliability.")
#             else:
#                 reasoning_parts.append("Information does not come from official company sources, reducing accuracy score.")
        
#         # Summary statement
#         if overall > 75:
#             reasoning_parts.append(f"Overall, this is high-quality contact information with good coverage across multiple channels.")
#         elif overall > 50:
#             reasoning_parts.append(f"Overall, this is adequate contact information but has some gaps in coverage.")
#         else:
#             reasoning_parts.append(f"Overall, this contact information is incomplete and may not be reliable for all communication needs.")
        
#         # Join reasoning parts with spaces
#         reasoning = " ".join(reasoning_parts)
        
#         return {
#             "overall_score": overall,
#             "confidence": confidence,
#             "completeness": completeness,
#             "accuracy": accuracy,
#             "reasoning": reasoning
#         }
    
#     def _extract_phones(self, text):
#         """Extract phone numbers from text"""
#         patterns = [
#             r'\b(?:0\d{2,4}[-\s]?\d{3,4}[-\s]?\d{3,4})\b',
#             r'\b(?:\+44|0)[-\s]?[0-9]{3,4}[-\s]?[0-9]{3,4}[-\s]?[0-9]{3,4}\b',
#             r'\b(?:\(\d{3,5}\)[-\s]?\d{3,4}[-\s]?\d{3,4})\b',
#             r'Phone(?:\s*Number)?:?\s*([+0-9\s\-()]{7,})',
#             r'(?:Telephone|Tel)(?:\s*Number)?:?\s*([+0-9\s\-()]{7,})'
#         ]
        
#         phones = []
#         for pattern in patterns:
#             matches = re.finditer(pattern, text, re.IGNORECASE)
#             for match in matches:
#                 if len(match.groups()) > 0:
#                     phone = match.group(1).strip()
#                 else:
#                     phone = match.group(0).strip()
#                 if phone and phone not in phones:
#                     phones.append(phone)
        
#         return phones
    
#     def _extract_emails(self, text):
#         """Extract email addresses from text"""
#         email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
#         return list(set(re.findall(email_pattern, text)))
    
#     def _extract_website(self, text):
#         """Extract website from text"""
#         # Try to extract a mentioned website
#         website_patterns = [
#             r'Website(?:\s*URL)?:?\s*(https?://[^\s,]+)',
#             r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b[-a-zA-Z0-9()@:%_\+.~#?&//=]*'
#         ]
        
#         for pattern in website_patterns:
#             matches = re.finditer(pattern, text, re.IGNORECASE)
#             for match in matches:
#                 if len(match.groups()) > 0:
#                     return match.group(1).strip()
#                 return match.group(0).strip()
        
#         return ""
    
#     def _extract_address(self, text):
#         """Extract physical address from text"""
#         address_patterns = [
#             r'(?:Address|Location):\s*([^,]+(,\s*[^,]+){2,})',
#             r'(?:Address|Location)[^\n\r]+([\w\s]+,\s*[\w\s]+(?:,\s*[\w\s]+)+)',
#             r'(?:Address|Location)(?:[^\n:]*?):?\s*([A-Za-z0-9\s,]+(?:Road|Street|Ave|Avenue|Lane|Drive|Way|Court|Plaza|Boulevard|Blvd|Rd|St|Dr|Ln)[^\.;]*)'
#         ]
        
#         for pattern in address_patterns:
#             match = re.search(pattern, text, re.IGNORECASE)
#             if match and len(match.groups()) > 0:
#                 return match.group(1).strip()
        
#         return ""
    
#     def _save_bulk_results(
#         self, 
#         results: List[Dict[str, Any]],
#         query: str = "",
#         with_evaluation: bool = False
#     ):
#         """
#         Save bulk search results to a CSV file with structured contact information columns
        
#         Args:
#             results (List[Dict]): Search results to save
#             query (str): The query that was used for the search
#             with_evaluation (bool): Whether evaluation data is included
        
#         Returns:
#             str: The full absolute path to the saved file
#         """
#         # Generate filename
#         timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
#         # Create a safe filename by removing spaces and special characters
#         safe_query = re.sub(r'[^\w\s]', '', query).replace(' ', '_')
        
#         # Add evaluation indicator if included
#         eval_indicator = "_evaluated" if with_evaluation else ""
        
#         # Generate the full filename with path
#         base_filename = f"bulk_search_{safe_query}{eval_indicator}_{timestamp}.csv"
#         full_path = os.path.join(self.output_dir, base_filename)
        
#         print(f"Saving bulk results to: {full_path} (directory: {self.output_dir})")
        
#         # Make sure the output directory exists
#         os.makedirs(self.output_dir, exist_ok=True)
        
#         # Prepare CSV headers with explicit contact information columns
#         if with_evaluation:
#             headers = [
#                 'Name', 
#                 'Email', 
#                 'Phone', 
#                 'Website', 
#                 'Address',
#                 'Detailed_Contact_Info',  # New column for structured contact info
#                 'Rating', 
#                 'Confidence', 
#                 'Completeness', 
#                 'Accuracy', 
#                 'Reasoning', 
#                 'MilesAI_Response'
#             ]
#         else:
#             headers = [
#                 'Name', 
#                 'Email', 
#                 'Phone', 
#                 'Website', 
#                 'Address',
#                 'Detailed_Contact_Info',  # New column for structured contact info
#                 'MilesAI_Response'
#             ]
        
#         # Write results to CSV
#         with open(full_path, 'w', newline='', encoding='utf-8') as csvfile:
#             writer = csv.writer(csvfile)
#             writer.writerow(headers)
            
#             for result in results:
#                 # Get miles_ai response
#                 miles_response = result.get('MilesAI_Response', '')
                
#                 # Get contact information from the LLM extraction results
#                 contact_info = result.get('Contact_Info', {})
    
#                 # Debug print to verify what we're getting
#                 print(f"Processing result for: {result.get('Name')}")
#                 print(f"Contact info: {contact_info}")
                
#                 # Handle emails list - with improved structure handling
#                 emails = contact_info.get('emails', [])
#                 emails_list = []
                
#                 if isinstance(emails, list):
#                     for email in emails:
#                         if isinstance(email, dict) and 'address' in email:
#                             # Structured format with description
#                             desc = email.get('description', '')
#                             if desc:
#                                 emails_list.append(f"{email['address']} ({desc})")
#                             else:
#                                 emails_list.append(email['address'])
#                         elif isinstance(email, str):
#                             # Simple string format
#                             emails_list.append(email)
                
#                 emails_str = ', '.join(emails_list) if emails_list else ''
                
#                 # Handle phones list - with improved structure handling
#                 phones = contact_info.get('phones', [])
#                 phones_list = []
                
#                 if isinstance(phones, list):
#                     for phone in phones:
#                         if isinstance(phone, dict) and 'number' in phone:
#                             # Structured format with description
#                             desc = phone.get('description', '')
#                             if desc:
#                                 phones_list.append(f"{phone['number']} ({desc})")
#                             else:
#                                 phones_list.append(phone['number'])
#                         elif isinstance(phone, str):
#                             # Simple string format
#                             phones_list.append(phone)
                
#                 phones_str = ', '.join(phones_list) if phones_list else ''
                
#                 # Get website and address
#                 website = contact_info.get('website', '')
#                 address = contact_info.get('address', '')
                
#                 # Create detailed contact info parts list
#                 detailed_info_parts = []
                
#                 # Format structured phone numbers for the detailed info
#                 if isinstance(phones, list):
#                     phone_lines = ["PHONE NUMBERS:"]
                    
#                     # Handle both dictionary and string formats
#                     for phone in phones:
#                         if isinstance(phone, dict) and 'number' in phone:
#                             desc = phone.get('description', 'Main')
#                             phone_lines.append(f"{desc}: {phone['number']}")
#                         elif isinstance(phone, str):
#                             phone_lines.append(f"Main: {phone}")
                    
#                     detailed_info_parts.append("\n".join(phone_lines))
                
#                 # Format structured email addresses for the detailed info
#                 if isinstance(emails, list):
#                     email_lines = ["EMAIL ADDRESSES:"]
                    
#                     # Handle both dictionary and string formats
#                     for email in emails:
#                         if isinstance(email, dict) and 'address' in email:
#                             desc = email.get('description', 'General')
#                             email_lines.append(f"{desc}: {email['address']}")
#                         elif isinstance(email, str):
#                             email_lines.append(f"General: {email}")
                    
#                     detailed_info_parts.append("\n".join(email_lines))
                
#                 # Add additional locations if present
#                 additional_locations = contact_info.get('additional_locations', [])
#                 if additional_locations:
#                     location_lines = ["ADDITIONAL LOCATIONS:"]
#                     for location in additional_locations:
#                         if isinstance(location, dict):
#                             loc_name = location.get('name', '')
#                             loc_address = location.get('address', '')
#                             loc_phone = location.get('phone', '')
#                             location_lines.append(f"{loc_name}: {loc_address} - {loc_phone}")
#                     detailed_info_parts.append("\n".join(location_lines))
                
#                 # Join all parts to create the detailed contact info
#                 detailed_contact_info = "\n\n".join(detailed_info_parts)
                
#                 # Create row data
#                 row_data = [
#                     result.get('Name', ''),  # Simply use the Name exactly as provided in the search
#                     emails_str,
#                     phones_str,
#                     website,
#                     address,
#                     detailed_contact_info  # Add the detailed contact info
#                 ]
                
#                 # Add evaluation data if needed
#                 if with_evaluation and "Evaluation" in result:
#                     evaluation = result.get('Evaluation', {})
                    
#                     # Extract evaluation scores
#                     overall = max(30, int(float(evaluation.get('overall_score', 60))))
#                     confidence = max(30, int(float(evaluation.get('confidence', 60))))
#                     completeness = max(30, int(float(evaluation.get('completeness', 60))))
#                     accuracy = max(30, int(float(evaluation.get('accuracy', 60))))
#                     reasoning = evaluation.get('reasoning', '') or self._generate_detailed_evaluation(
#                         result.get('Name', ''), 
#                         miles_response, 
#                         result.get('Sources', [])
#                     )['reasoning']
                    
#                     # Add evaluation data to row
#                     row_data.extend([overall, confidence, completeness, accuracy, reasoning, miles_response])
#                 else:
#                     # Add just the miles response for non-evaluated results
#                     row_data.append(miles_response)
                
#                 # Write the row
#                 writer.writerow(row_data)
#                 print(f"Wrote row with data: {row_data[:5]}")
        
#         print(f"Bulk search results saved to {full_path}")
        
#         # Save JSON with full data
#         json_path = os.path.splitext(full_path)[0] + ".json"
#         try:
#             with open(json_path, 'w', encoding='utf-8') as jsonfile:
#                 json.dump(results, jsonfile, indent=2, ensure_ascii=False)
            
#             print(f"Full detailed results saved to {json_path}")
#         except Exception as e:
#             print(f"Error saving JSON results: {e}")
        
#         # Return the full path
#         return full_path
    
#     def interactive_bulk_search(self, prowler=None):
#         """
#         Interactive method to perform bulk searches
#         Allows user to input names and custom search query
        
#         Args:
#             prowler: Optional evaluator object
#         """
#         print("Bulk Information Search")
#         print("-" * 30)
        
#         # Get input method
#         input_method = input("Enter names from (1) Console, (2) File: ").strip()
        
#         # Get names
#         if input_method == '1':
#             names = input("Enter names/businesses (comma-separated): ").split(',')
#             names = [name.strip() for name in names]
#         elif input_method == '2':
#             filepath = input("Enter file path (CSV or text, one name per line): ").strip()
#             try:
#                 with open(filepath, 'r') as f:
#                     names = [line.strip() for line in f if line.strip()]
#             except FileNotFoundError:
#                 print("File not found. Exiting.")
#                 return
#         else:
#             print("Invalid input method. Exiting.")
#             return
        
#         # Get search query
#         query = input("Enter your search query: ").strip()
        
#         # Always use evaluation if available
#         if not prowler and self.evaluator:
#             prowler = self.evaluator
        
#         # Perform search
#         self.bulk_search(names, query, prowler=prowler)
        
#         print("\nBulk search completed.")

# def main():
#     """
#     Standalone function to run bulk contact finder
#     """

# if __name__ == "__main__":
#     main()

import os
import csv
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
    Uses LLM for extraction and evaluation
    """
    
    def __init__(self, config_path: str = "config.json", output_dir: str = "contact_search_results"):
        """
        Initialize BulkContactFinder
        
        Args:
            config_path (str): Path to configuration file
            output_dir (str): Directory to save search results
        """
        self.contact_finder = ContactFinder(config_path)
        
        # Initialize evaluator if available
        self.evaluator = None
        if EVALUATOR_AVAILABLE:
            try:
                self.evaluator = ContactEvaluator(config_path)
                print("ContactEvaluator initialized successfully")
            except Exception as e:
                print(f"Warning: Failed to initialize ContactEvaluator: {e}")
        
        # Convert output_dir to absolute path based on the current working directory
        # This ensures we always save files in a consistent location
        self.output_dir = os.path.abspath(output_dir)
        print(f"BulkContactFinder initialized with output directory: {self.output_dir}")
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
    
    def bulk_search(
        self, 
        names: List[str], 
        query: str, 
        save_full_results: bool = True,
        prowler = None,  # Optional prowler evaluator
        progress_callback = None  # Parameter for progress reporting
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
                print(f"Searching for contact information for: {name} {query}")
                
                # Initialize selenium scraper
                print("Initializing Selenium scraper...")
                from selenium_scraper import SeleniumScraper
                scraper = SeleniumScraper(headless=True)
                
                # Search for relevant URLs
                search_query = f"{name} {query}"
                urls = scraper.search(search_query)
                print(f"Found {len(urls)} search results")
                
                # Look for contact pages specifically
                contact_urls = []
                for url in urls:
                    # Prioritize contact-us pages
                    if 'contact' in url.lower():
                        contact_urls.insert(0, url)
                    else:
                        contact_urls.append(url)
                
                # Make sure we have at least some URLs
                if not contact_urls:
                    contact_urls = urls
                
                # Initialize results
                result_text = ""
                scraped_contents = []
                
                # Visit and scrape each URL (especially contact pages)
                print("Scraping contact pages for detailed information...")
                for url in contact_urls[:3]:  # Limit to first 3 URLs to avoid too much scraping
                    print(f"Scraping URL: {url}")
                    page_result = scraper.scrape_url(url)
                    
                    if page_result and 'content' in page_result and page_result['content']:
                        # Add the page content to our results
                        scraped_contents.append(f"URL: {url}\n{page_result['content']}")
                
                # Close the scraper when done
                scraper.close()
                print("Browser closed")
                
                # Combine all scraped content
                if scraped_contents:
                    result_text = "\n\n---\n\n".join(scraped_contents)
                else:
                    result_text = "No content could be extracted from the URLs."
                
                # Store the complete results
                result_entry = {
                    "Name": name,
                    "Query": query,
                    "MilesAI_Response": result_text,  # Complete content from all pages
                    "Sources": contact_urls
                }
                
                # Use LLM-based extraction
                contact_info = self._extract_contact_info_with_llm(name, result_text, contact_urls)
                
                # Store the extracted results
                result_entry["Contact_Info"] = contact_info
                
                # Evaluate results if evaluator is available
                if evaluator:
                    try:
                        print(f"Evaluating results for {name}...")
                        time.sleep(1)  # Small delay to avoid overwhelming the API
                        
                        # Use the contact info for evaluation
                        phones = []
                        for phone in contact_info.get("phones", []):
                            if isinstance(phone, dict) and "number" in phone:
                                phones.append(phone["number"])
                        
                        emails = []
                        for email in contact_info.get("emails", []):
                            if isinstance(email, dict) and "address" in email:
                                emails.append(email["address"])
                        
                        website = contact_info.get("website", "")
                        address = contact_info.get("address", "")
                        
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
                        
                        # Query evaluator with explicit instructions
                        prompt = f"""Evaluate the following contact information extracted for {name}:

                                CONTACT INFORMATION SUMMARY:
                                {found_summary if found_items else "No structured contact information found"}

                                FULL EXTRACTED TEXT:
                                {result_text[:800] if len(result_text) > 800 else result_text}

                                SOURCE URLS: {'; '.join(contact_urls[:3]) if contact_urls else 'No sources provided'}

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
                        # Query the model directly
                        raw_result = evaluator.evaluator.model_manager.query_model(prompt)
                        print(f"Raw evaluation (first 200 chars): {raw_result[:200]}...")
                        
                        # Try to extract JSON data from the response
                        try:
                            # First try direct JSON parsing
                            evaluation = json.loads(raw_result)
                        except json.JSONDecodeError:
                            # Try to extract JSON object using regex
                            import re
                            json_match = re.search(r'(\{[^{]*"overall_score"[^}]*\})', raw_result, re.DOTALL)
                            if json_match:
                                try:
                                    json_str = json_match.group(0)
                                    evaluation = json.loads(json_str)
                                except:
                                    # Generate fallback evaluation
                                    evaluation = self._generate_evaluation(name, contact_info, contact_urls)
                            else:
                                # No JSON found, generate evaluation
                                evaluation = self._generate_evaluation(name, contact_info, contact_urls)
                        
                        # Ensure scores are within valid range
                        for key in ["overall_score", "confidence", "completeness", "accuracy"]:
                            if key not in evaluation or not evaluation[key] or evaluation[key] < 20:
                                evaluation[key] = 60  # Default fallback score
                        
                        # Store the evaluation
                        result_entry["Evaluation"] = evaluation
                        
                        # Print reasoning for debugging
                        print(f"Reasoning: {evaluation.get('reasoning', 'No reasoning provided')}")
                        
                        # Create simplified output format
                        phones_str = ', '.join(phones) if phones else ''
                        emails_str = ', '.join(emails) if emails else ''
                        contact_summary = f"Phone: {phones_str}, Email: {emails_str}, Website: {website}"
                        
                        confidence = evaluation.get("confidence", 70) / 100
                        result_entry["Simplified"] = f"{name}, {contact_summary}, rating: {confidence:.1f}"
                        
                        print(f"Evaluation scores: Overall={evaluation.get('overall_score')}, Confidence={evaluation.get('confidence')}, Completeness={evaluation.get('completeness')}, Accuracy={evaluation.get('accuracy')}")
                    
                    except Exception as eval_err:
                        print(f"Error during evaluation: {eval_err}")
                        # Generate fallback evaluation
                        evaluation = self._generate_evaluation(name, contact_info, contact_urls)
                        result_entry["Evaluation"] = evaluation
                        
                        # Simple output format
                        phones_str = ', '.join(phones) if phones else ''
                        emails_str = ', '.join(emails) if emails else ''
                        contact_summary = f"Phone: {phones_str}, Email: {emails_str}, Website: {website}"
                        
                        confidence = evaluation.get("confidence", 65) / 100
                        result_entry["Simplified"] = f"{name}, {contact_summary}, rating: {confidence:.1f}"
                
                bulk_results.append(result_entry)
                
                # Call the progress callback if provided
                if progress_callback and callable(progress_callback):
                    progress_callback(name)
                
            except Exception as search_err:
                print(f"Error searching for {name}: {search_err}")
                import traceback
                traceback.print_exc()
                
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
    
    def _extract_contact_info_with_llm(self, name, text, urls):
        """
        Use the LLM to extract structured contact information with context
        
        Args:
            name (str): Business name
            text (str): Text to extract information from
            urls (list): Source URLs
            
        Returns:
            dict: Structured contact information
        """
        # Clean and preprocess the text to make it more suitable for LLM extraction
        # Remove very long HTML sections, excessive whitespace, and non-essential content
        
        # Limit text size and focus on the most important parts
        text_for_extraction = self._preprocess_text_for_llm(text)
        
        # Create a prompt specifically for contact information extraction
        prompt = f"""You are Miles AI, a specialized contact information extraction assistant.
        
        TASK: Extract ALL contact information for "{name}" from the following text.
        
        TEXT:
        {text_for_extraction}
        
        SOURCE URLS: {'; '.join(urls[:3]) if urls else 'No sources provided'}
        
        Extract and return ONLY the following information in JSON format:
        {{
            "business_name": "The most complete official name found",
            "phones": [
                {{"number": "Phone number 1", "description": "Department or purpose of this phone number"}},
                {{"number": "Phone number 2", "description": "Department or purpose of this phone number"}}
            ],
            "emails": [
                {{"address": "Email address 1", "description": "Department or purpose of this email"}},
                {{"address": "Email address 2", "description": "Department or purpose of this email"}}
            ],
            "website": "Main website URL",
            "address": "The primary physical address with postal code",
            "additional_locations": [
                {{"name": "Location name", "address": "Full address", "phone": "Location phone number"}}
            ]
        }}
        
        CRITICAL INSTRUCTIONS:
        1. Search through the text and extract ALL phone numbers and email addresses you can find
        2. For each phone number, INCLUDE what it's for (e.g., "Main Switchboard", "Appointments", "Ward 5")
        3. For each email address, INCLUDE what it's for (e.g., "General Inquiries", "Support", "Sales Team")
        4. If there are multiple locations or branches, list them with their contact details
        5. ENSURE your response is valid, parseable JSON - this is critical
        6. For website, ONLY include the main domain (e.g., "https://example.com")
        7. If you can't find certain information, use empty arrays or empty strings, but MAINTAIN the JSON structure
        8. DO NOT include explanations or notes outside the JSON structure
        
        YOUR ENTIRE RESPONSE MUST BE VALID JSON ONLY. Do not include anything else.
        """
        
        # Query the model via the contact_finder
        if hasattr(self.contact_finder, 'model_manager') and self.contact_finder.model_manager:
            try:
                raw_result = self.contact_finder.model_manager.query_model(prompt)
            except Exception as e:
                print(f"Error querying model: {e}")
                return self._process_extraction_fallback(name, text, urls)
        elif self.evaluator and hasattr(self.evaluator, 'evaluator') and hasattr(self.evaluator.evaluator, 'model_manager'):
            try:
                raw_result = self.evaluator.evaluator.model_manager.query_model(prompt)
            except Exception as e:
                print(f"Error querying evaluator model: {e}")
                return self._process_extraction_fallback(name, text, urls)
        else:
            print("Warning: No model available for contact extraction")
            return self._process_extraction_fallback(name, text, urls)
        
        # Process and validate the LLM response
        return self._process_llm_response(raw_result, name, text, urls)

    def _preprocess_text_for_llm(self, text):
        """
        Preprocesses the text to improve LLM extraction success
        
        Args:
            text (str): The raw text to preprocess
            
        Returns:
            str: Preprocessed text
        """
        import re
        
        # If text is too large, focus on the most relevant parts
        if len(text) > 15000:
            # Extract chunks that are likely to contain contact information
            chunks = []
            
            # Look for sections with contact-related keywords
            contact_sections = re.findall(r'(?i)(?:contact|phone|email|address|location|get in touch|reach us)[\s\S]{1,1000}?(?:\n\n|\Z)', text)
            for section in contact_sections[:5]:  # Limit to 5 most relevant sections
                if len(section) > 100:  # Only include substantial sections
                    chunks.append(section)
            
            # If no contact sections found, include the beginning and end of the text
            if not chunks:
                chunks.append(text[:5000])  # First 5000 chars
                if len(text) > 10000:
                    chunks.append(text[-5000:])  # Last 5000 chars
            
            # Combine chunks
            preprocessed_text = "\n\n".join(chunks)
        else:
            preprocessed_text = text
        
        # Clean up the text
        preprocessed_text = re.sub(r'\s+', ' ', preprocessed_text)  # Collapse whitespace
        preprocessed_text = re.sub(r'(?i)(?:cookie|gdpr|privacy policy|terms of use)[\s\S]{1,200}?(?:\n\n|\Z)', '', preprocessed_text)  # Remove cookie notices
        
        return preprocessed_text[:15000]  # Final size limit

    def _process_llm_response(self, raw_result, name, text, urls):
        """
        Process the LLM response and handle various failure modes
        
        Args:
            raw_result (str): Raw response from LLM
            name (str): Business name
            text (str): Original text
            urls (list): Source URLs
            
        Returns:
            dict: Structured contact information
        """
        import re
        import json
        
        if not raw_result or len(raw_result.strip()) < 10:
            print("Warning: Received empty or very short response from LLM")
            return self._extract_basic_contacts(name, text, urls)
        
        # Try multiple methods to extract valid JSON from the response
        try:
            # Method 1: Direct JSON parsing of the whole response
            contact_info = json.loads(raw_result)
            print("Successfully parsed full JSON response")
            self._ensure_all_fields(contact_info, name, urls)
            return contact_info
        except json.JSONDecodeError:
            print("Initial JSON parsing failed, trying cleanup methods...")
            
            # Method 2: Clean up common JSON formatting issues
            try:
                # Remove markdown code blocks
                cleaned_text = raw_result.strip()
                if "```json" in cleaned_text:
                    cleaned_text = re.sub(r'```json\s+', '', cleaned_text)
                    cleaned_text = re.sub(r'\s+```', '', cleaned_text)
                elif "```" in cleaned_text:
                    cleaned_text = re.sub(r'```\s+', '', cleaned_text)
                    cleaned_text = re.sub(r'\s+```', '', cleaned_text)
                
                # Fix unbalanced braces
                bracket_diff = cleaned_text.count('{') - cleaned_text.count('}')
                if bracket_diff > 0:
                    cleaned_text += '}' * bracket_diff
                    print(f"Fixed unbalanced brackets by adding {bracket_diff} closing braces")
                
                # Try parsing the cleaned JSON
                contact_info = json.loads(cleaned_text)
                print("Successfully parsed cleaned JSON")
                self._ensure_all_fields(contact_info, name, urls)
                return contact_info
            except json.JSONDecodeError:
                print("Cleaned JSON parsing failed, trying regex extraction...")
                
                # Method 3: Use regex to extract the JSON object
                try:
                    # Look for a JSON object
                    json_match = re.search(r'(\{[\s\S]*\})', cleaned_text)
                    if json_match:
                        json_str = json_match.group(1)
                        # Further clean the JSON string
                        json_str = re.sub(r',\s*}', '}', json_str)  # Remove trailing commas
                        contact_info = json.loads(json_str)
                        print("Successfully extracted JSON via regex")
                        self._ensure_all_fields(contact_info, name, urls)
                        return contact_info
                except Exception:
                    print("Regex JSON extraction failed, falling back to direct extraction...")
        
        # If all JSON parsing methods fail, extract contact info directly
        return self._extract_basic_contacts(name, text, urls)

    def _extract_basic_contacts(self, name, text, urls):
        """
        Extract basic contact information using pattern matching when LLM fails
        
        Args:
            name (str): Business name
            text (str): Text to extract from
            urls (list): Source URLs
            
        Returns:
            dict: Basic contact information
        """
        import re
        
        # Extract website from URLs if available
        website = ""
        if urls and len(urls) > 0:
            for url in urls:
                if '://' in url:
                    parts = url.split('://')
                    if len(parts) > 1:
                        domain_parts = parts[1].split('/')
                        if domain_parts:
                            website = f"{parts[0]}://{domain_parts[0]}"
                            break
        
        # Extract email addresses
        emails = []
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_matches = re.findall(email_pattern, text)
        for email in set(email_matches):
            purpose = "General"
            if 'info' in email:
                purpose = "Information"
            elif 'support' in email:
                purpose = "Support"
            elif 'contact' in email:
                purpose = "Contact"
            emails.append({"address": email, "description": purpose})
        
        # Extract phone numbers (focused on UK formats)
        phones = []
        phone_patterns = [
            r'(?:Tel|Telephone|Phone)(?:\.|\:)?\s*(\+?[0-9][0-9\s\-]{7,16})',  # Phone: 01234 567890
            r'(?:Tel|Telephone|Phone)(?:\.|\:)?\s*([0-9][0-9\s\-]{7,16})',     # Tel: 01234 567890
            r'([0-9]{4,5}\s*[0-9]{3}\s*[0-9]{3,4})',                          # 01234 567 890
            r'([0-9]{5}\s*[0-9]{6})',                                         # 01234 567890
            r'(\+44\s*[0-9\s\-]{10,14})'                                      # +44 1234 567890
        ]
        
        for pattern in phone_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                phone_number = match.group(1).strip() if len(match.groups()) > 0 else match.group(0).strip()
                
                # Look for department context before the phone number
                context_start = max(0, match.start() - 50)
                context = text[context_start:match.start()]
                
                # Default purpose
                purpose = "Main"
                
                # Check for department names in context
                dept_match = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3}):?\s*$', context)
                if dept_match:
                    purpose = dept_match.group(1).strip()
                
                phones.append({"number": phone_number, "description": purpose})
        
        # Extract address (simplified)
        address = ""
        address_patterns = [
            r'(?:Address|Location)(?::|is)?([^,\n]+(,\s*[^,\n]+){2,})',
            r'([A-Z0-9][A-Za-z0-9\s\,]+,[A-Za-z\s]+,[A-Za-z\s]+,[A-Z]{1,2}[0-9][0-9A-Z]?\s?[0-9][A-Z]{2})'  # UK address with postcode
        ]
        
        for pattern in address_patterns:
            address_match = re.search(pattern, text)
            if address_match:
                address = address_match.group(1).strip()
                break
        
        # Construct the result
        contact_info = {
            "business_name": self._extract_business_name(name, text),
            "phones": phones,
            "emails": emails,
            "website": website,
            "address": address,
            "additional_locations": []
        }
        
        return contact_info

    def _extract_business_name(self, default_name, text):
        """
        Extract business name from text when possible
        
        Args:
            default_name (str): Default business name
            text (str): Text to extract from
            
        Returns:
            str: Business name
        """
        import re
        
        # Try to extract from title or heading
        title_match = re.search(r'<title>([^|<]+)', text)
        if title_match:
            title = title_match.group(1).strip()
            if '|' in title:
                title = title.split('|')[0].strip()
            if title and len(title) > 3 and len(title) < 100:
                return title
        
        # Try to extract from page title if present
        page_title_match = re.search(r'Page title: ([^\n]+)', text)
        if page_title_match:
            title = page_title_match.group(1).strip()
            if '|' in title:
                title = title.split('|')[0].strip()
            if title and len(title) > 3 and len(title) < 100:
                return title
        
        # Default to the provided name
        return default_name

    def _process_extraction_fallback(self, name, text, urls):
        """
        Create minimal contact info when extraction fails
        
        Args:
            name (str): Business name
            text (str): Original text
            urls (list): Source URLs
            
        Returns:
            dict: Basic contact information
        """
        # Extract website from URLs
        website = ""
        if urls and len(urls) > 0:
            url = urls[0]
            if '://' in url:
                parts = url.split('://')
                if len(parts) > 1:
                    domain_parts = parts[1].split('/')
                    if domain_parts:
                        website = f"{parts[0]}://{domain_parts[0]}"
        
        return {
            "business_name": name,
            "phones": [],
            "emails": [],
            "website": website,
            "address": "",
            "additional_locations": []
        }

    def _ensure_all_fields(self, contact_info, name, urls):
        """
        Ensure all fields exist in the contact info
        
        Args:
            contact_info (dict): Contact information
            name (str): Business name
            urls (list): Source URLs
        """
        if not contact_info.get("business_name"):
            contact_info["business_name"] = name
            
        if "phones" not in contact_info:
            contact_info["phones"] = []
            
        if "emails" not in contact_info:
            contact_info["emails"] = []
            
        if not contact_info.get("website") and urls and len(urls) > 0:
            # Get domain from first URL
            url = urls[0]
            if '://' in url:
                parts = url.split('://')
                if len(parts) > 1:
                    domain = parts[1].split('/')[0]
                    contact_info["website"] = f"{parts[0]}://{domain}"
            else:
                contact_info["website"] = ""
        
        if "address" not in contact_info:
            contact_info["address"] = ""
            
        if "additional_locations" not in contact_info:
            contact_info["additional_locations"] = []
    
    def _generate_evaluation(self, name, contact_info, urls):
        """
        Generate a basic evaluation when the evaluator model fails
        
        Args:
            name (str): Business name
            contact_info (dict): Extracted contact information
            urls (list): Source URLs
            
        Returns:
            dict: Evaluation scores and reasoning
        """
        # Count contact items
        phone_count = len(contact_info.get("phones", []))
        email_count = len(contact_info.get("emails", []))
        has_website = bool(contact_info.get("website", ""))
        has_address = bool(contact_info.get("address", ""))
        
        # Calculate scores based on available information
        completeness = 60  # Base score
        if phone_count > 0:
            completeness += min(20, phone_count * 5)  # Max +20 for phones
        else:
            completeness -= 15
            
        if email_count > 0:
            completeness += min(15, email_count * 5)  # Max +15 for emails
        else:
            completeness -= 10
            
        if has_website:
            completeness += 10
        else:
            completeness -= 5
            
        if has_address:
            completeness += 15
        else:
            completeness -= 10
        
        # Determine confidence based on sources
        confidence = 65  # Base confidence
        if urls:
            # Higher confidence if URLs contain the company name or are official looking
            for url in urls:
                if name.lower().replace(" ", "") in url.lower().replace(" ", ""):
                    confidence += 15
                    break
                    
            if len(urls) >= 3:
                confidence += 5  # More sources = higher confidence
        
        # Calculate accuracy based on sources and information consistency
        accuracy = 70  # Base accuracy
        if not urls:
            accuracy -= 20  # No sources = lower accuracy
        
        # Calculate overall score (weighted average)
        overall = int((completeness * 0.4) + (confidence * 0.3) + (accuracy * 0.3))
        
        # Ensure all scores are within 30-95 range
        completeness = max(30, min(95, completeness))
        confidence = max(30, min(95, confidence))
        accuracy = max(30, min(95, accuracy))
        overall = max(30, min(95, overall))
        
        # Generate reasoning
        reasoning_parts = []
        
        # Information analysis
        if phone_count > 0 and email_count > 0:
            reasoning_parts.append(f"Found {phone_count} phone numbers and {email_count} email addresses, providing good communication options.")
        elif phone_count > 0:
            reasoning_parts.append(f"Found {phone_count} phone numbers but no email addresses, limiting digital communication options.")
        elif email_count > 0:
            reasoning_parts.append(f"Found {email_count} email addresses but no phone numbers, missing direct voice contact options.")
        else:
            reasoning_parts.append("No phone numbers or email addresses found, severely limiting contact options.")
        
        # Website analysis
        if has_website:
            website = contact_info.get("website", "")
            if name.lower().replace(" ", "") in website.lower().replace(" ", ""):
                reasoning_parts.append(f"Found official website {website} that increases confidence in the information.")
            else:
                reasoning_parts.append(f"Found website {website} but it may not be the official company site.")
        else:
            reasoning_parts.append("No website URL found, reducing completeness score.")
        
        # Address analysis
        if has_address:
            reasoning_parts.append("Found physical address information, which improves completeness and provides offline contact options.")
        else:
            reasoning_parts.append("No physical address found, which reduces the completeness score significantly.")
        
        # Sources analysis
        if urls:
            reasoning_parts.append(f"Information comes from {len(urls)} source URLs, which {'increases' if len(urls) >= 2 else 'supports'} confidence in the accuracy.")
        else:
            reasoning_parts.append("No source URLs available, which greatly reduces confidence in the information.")
        
        # Join reasoning parts
        reasoning = " ".join(reasoning_parts)
        
        return {
            "overall_score": overall,
            "confidence": confidence,
            "completeness": completeness,
            "accuracy": accuracy,
            "reasoning": reasoning
        }
    
    def _save_bulk_results(
        self, 
        results: List[Dict[str, Any]],
        query: str = "",
        with_evaluation: bool = False
    ) -> str:
        """
        Save bulk search results to a CSV file with structured contact information columns
        
        Args:
            results (List[Dict]): Search results to save
            query (str): The query that was used for the search
            with_evaluation (bool): Whether evaluation data is included
        
        Returns:
            str: The full absolute path to the saved file
        """
        import csv
        import os
        import re
        import json
        from datetime import datetime
        
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
        
        # Prepare CSV headers with explicit contact information columns
        if with_evaluation:
            headers = [
                'Name', 
                'Email', 
                'Phone', 
                'Website', 
                'Address',
                'Detailed_Contact_Info',  # New column for structured contact info
                'Rating', 
                'Confidence', 
                'Completeness', 
                'Accuracy', 
                'Reasoning'
            ]
        else:
            headers = [
                'Name', 
                'Email', 
                'Phone', 
                'Website', 
                'Address',
                'Detailed_Contact_Info'  # New column for structured contact info
            ]
        
        # Write results to CSV - ONE ROW PER COMPANY
        with open(full_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)
            
            for result in results:
                # Get contact information from the extraction results
                contact_info = result.get('Contact_Info', {})

                # Debug print to verify what we're getting
                print(f"Processing result for: {result.get('Name')}")
                
                # Handle emails list - with deduplication
                emails = contact_info.get('emails', [])
                seen_emails = set()
                emails_list = []
                
                if isinstance(emails, list):
                    for email in emails:
                        if isinstance(email, dict) and 'address' in email:
                            # Structured format with description
                            email_addr = email['address']
                            if email_addr in seen_emails:
                                continue
                                
                            seen_emails.add(email_addr)
                            desc = email.get('description', '')
                            if desc:
                                emails_list.append(f"{email_addr} ({desc})")
                            else:
                                emails_list.append(email_addr)
                        elif isinstance(email, str):
                            # Simple string format
                            if email in seen_emails:
                                continue
                                
                            seen_emails.add(email)
                            emails_list.append(email)
                
                emails_str = ', '.join(emails_list) if emails_list else ''
                
                # Handle phones list - with deduplication
                phones = contact_info.get('phones', [])
                seen_phones = set()
                phones_list = []
                
                if isinstance(phones, list):
                    for phone in phones:
                        if isinstance(phone, dict) and 'number' in phone:
                            # Structured format with description
                            phone_num = phone['number']
                            # Normalize phone for deduplication
                            norm_phone = re.sub(r'[\s\-\(\)\+]', '', phone_num)
                            
                            if norm_phone in seen_phones:
                                continue
                                
                            seen_phones.add(norm_phone)
                            desc = phone.get('description', '')
                            if desc:
                                phones_list.append(f"{phone_num} ({desc})")
                            else:
                                phones_list.append(phone_num)
                        elif isinstance(phone, str):
                            # Simple string format
                            norm_phone = re.sub(r'[\s\-\(\)\+]', '', phone)
                            if norm_phone in seen_phones:
                                continue
                                
                            seen_phones.add(norm_phone)
                            phones_list.append(phone)
                
                phones_str = ', '.join(phones_list) if phones_list else ''
                
                # Get website and address
                website = contact_info.get('website', '')
                address = contact_info.get('address', '')
                
                # Create detailed contact info parts list
                detailed_info_parts = []
                
                # Format structured phone numbers for the detailed info
                if isinstance(phones, list) and phones:
                    phone_lines = ["PHONE NUMBERS:"]
                    seen_numbers = set()
                    
                    for phone in phones:
                        if isinstance(phone, dict) and 'number' in phone:
                            num = phone.get('number', '')
                            # Normalize for deduplication check
                            norm_num = re.sub(r'[\s\-\(\)\+]', '', num)
                            
                            if norm_num in seen_numbers:
                                continue
                                
                            seen_numbers.add(norm_num)
                            desc = phone.get('description', 'Main')
                            phone_lines.append(f"{desc}: {num}")
                        elif isinstance(phone, str):
                            # Normalize for deduplication check
                            norm_num = re.sub(r'[\s\-\(\)\+]', '', phone)
                            
                            if norm_num in seen_numbers:
                                continue
                                
                            seen_numbers.add(norm_num)
                            phone_lines.append(f"Main: {phone}")
                    
                    detailed_info_parts.append("\n".join(phone_lines))
                
                # Format structured email addresses for the detailed info
                if isinstance(emails, list) and emails:
                    email_lines = ["EMAIL ADDRESSES:"]
                    seen_email_addrs = set()
                    
                    for email in emails:
                        if isinstance(email, dict) and 'address' in email:
                            addr = email.get('address', '')
                            
                            if addr in seen_email_addrs:
                                continue
                                
                            seen_email_addrs.add(addr)
                            desc = email.get('description', 'General')
                            email_lines.append(f"{desc}: {addr}")
                        elif isinstance(email, str):
                            if email in seen_email_addrs:
                                continue
                                
                            seen_email_addrs.add(email)
                            email_lines.append(f"General: {email}")
                    
                    detailed_info_parts.append("\n".join(email_lines))
                
                # Add additional locations if present
                additional_locations = contact_info.get('additional_locations', [])
                if additional_locations:
                    location_lines = ["ADDITIONAL LOCATIONS:"]
                    for location in additional_locations:
                        if isinstance(location, dict):
                            loc_name = location.get('name', '')
                            loc_addr = location.get('address', '')
                            loc_phone = location.get('phone', '')
                            location_lines.append(f"{loc_name}: {loc_addr} - {loc_phone}")
                    detailed_info_parts.append("\n".join(location_lines))
                
                # Join all parts to create the detailed contact info
                detailed_contact_info = "\n\n".join(detailed_info_parts)
                
                # Create row data - ONE ROW PER COMPANY
                row_data = [
                    result.get('Name', ''),  # Simply use the Name exactly as provided in the search
                    emails_str,
                    phones_str,
                    website,
                    address,
                    detailed_contact_info  # Add the detailed contact info
                ]
                
                # Add evaluation data if needed
                if with_evaluation and "Evaluation" in result:
                    evaluation = result.get('Evaluation', {})
                    
                    # Extract evaluation scores
                    overall = max(30, int(float(evaluation.get('overall_score', 60))))
                    confidence = max(30, int(float(evaluation.get('confidence', 60))))
                    completeness = max(30, int(float(evaluation.get('completeness', 60))))
                    accuracy = max(30, int(float(evaluation.get('accuracy', 60))))
                    reasoning = evaluation.get('reasoning', '') or ""
                    
                    # Add evaluation data to row
                    row_data.extend([overall, confidence, completeness, accuracy, reasoning])
                
                # Write ONE row per company
                writer.writerow(row_data)
                print(f"Wrote row with data: {row_data[:5]}")
        
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
    finder = BulkContactFinder()
    finder.interactive_bulk_search()

if __name__ == "__main__":
    main()