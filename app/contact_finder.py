from typing import Dict, List, Any, Tuple
from config_manager import ConfigManager
from model_manager import ModelManager
from web_scraper import WebScraper
from selenium_scraper import SeleniumScraper
import re
from bs4 import BeautifulSoup

class ContactFinder:
    """Main class that orchestrates the contact finding process"""
    
    def __init__(self, config_path: str = "config.json"):
        self.config_manager = ConfigManager(config_path)
        self.model_manager = ModelManager(self.config_manager)
        self.web_scraper = WebScraper(self.config_manager)
        self.selenium_scraper = None  # Will be initialised when needed
    
    def setup(self) -> bool:
        """Set up the contact finder by creating the custom model"""
        return self.model_manager.create_model()
    
    def _initialise_selenium(self):
        """Initialise the Selenium scraper if not already initialised"""
        if self.selenium_scraper is None:
            print("Initialising Selenium scraper...")
            headless = self.config_manager.get("headless", True)
            self.selenium_scraper = SeleniumScraper(headless=headless)
    
    def _cleanup_selenium(self):
        """Clean up Selenium resources when done"""
        if self.selenium_scraper is not None:
            self.selenium_scraper.close()
            self.selenium_scraper = None
    
    def initial_search(self, business_name: str) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Perform initial search and extract contact information from search results only.
        Returns contact information and a list of URLs for further scraping if needed.
        """
        verbose = self.config_manager.get("verbose")
        
        if verbose:
            print(f"Searching for contact information for: {business_name}")
        
        try:
            # Initialise Selenium
            self._initialise_selenium()
            
            # Step 1: Search for the business using Selenium
            max_results = self.config_manager.get("max_search_results", 5)
            search_results = self.selenium_scraper.search(business_name, max_results)
            
            if not search_results:
                return "No search results found. Please try a different search term.", []
            
            if verbose:
                print(f"Found {len(search_results)} search results")
            
            # Step 2: Extract information from search results pages
            search_page_data = {
                "urls": search_results,
                "search_term": business_name,
                "contact_info_from_search": self._extract_contact_info_from_selenium()
            }
            
            # Step 3: Format the data for the model
            formatted_data = self._format_search_data_for_model(business_name, search_page_data)
            
            # Step 4: Query the model to extract contact information with timeout
            if verbose:
                print("Extracting contact information from search results...")
            
            try:
                from concurrent.futures import ThreadPoolExecutor, TimeoutError
                
                with ThreadPoolExecutor() as executor:
                    future = executor.submit(self.model_manager.query_model, formatted_data)
                    
                    try:
                        # Set a 5-minute timeout
                        result = future.result(timeout=300)
                    except TimeoutError:
                        print("\nERROR: Model query timed out after 5 minutes.")
                        return "Model query timed out. Unable to extract contact information.", search_results
            except Exception as model_err:
                print(f"\nERROR during model query: {model_err}")
                return f"Error processing results: {model_err}", search_results
            
            return result, search_results
            
        except Exception as e:
            print(f"\nUnexpected error in initial search: {e}")
            return f"Unexpected error: {e}", []
        
        finally:
            # Clean up Selenium resources
            self._cleanup_selenium()
    
    def deep_scrape_url(self, url: str, business_name: str) -> str:
        """Scrape a specific URL for more detailed contact information"""
        verbose = self.config_manager.get("verbose")
        
        if verbose:
            print(f"Deep scraping URL: {url}")
        
        try:
            # Initialise Selenium
            self._initialise_selenium()
            
            # Scrape the specific URL using Selenium
            page_data = self.selenium_scraper.scrape_url(url)
            
            # Extract contact information from the page HTML
            self._enhance_page_data_with_contact_info(page_data)
            
            # Format data for the model
            formatted_data = self._format_url_data_for_model(business_name, url, page_data)
            
            # Query the model
            if verbose:
                print("Extracting detailed contact information...")
            
            result = self.model_manager.query_model(formatted_data)
            
            return result
            
        finally:
            # Clean up Selenium resources
            self._cleanup_selenium()
    
    def _extract_contact_info_from_selenium(self) -> Dict[str, List[str]]:
        """Extract contact information from the Selenium browser's current page"""
        if self.selenium_scraper is None:
            return {"phones": [], "emails": []}
        
        # Get the page source from Selenium
        page_source = self.selenium_scraper.driver.page_source
        
        # Use BeautifulSoup to parse the HTML
        soup = BeautifulSoup(page_source, "html.parser")
        
        # Extract text content
        text = soup.get_text(separator="\n", strip=True)
        
        # Extract contact info using our existing methods
        emails = self._extract_emails(text)
        phones = self._extract_phones(text)
        
        return {
            "emails": emails,
            "phones": phones
        }
    
    def _enhance_page_data_with_contact_info(self, page_data: Dict[str, Any]):
        """Extract contact information from page HTML and add it to page_data"""
        if not page_data.get("content"):
            return
        
        # Parse HTML content
        soup = BeautifulSoup(page_data["content"], "html.parser")
        
        # Extract text content
        text = soup.get_text(separator="\n", strip=True)
        page_data["text_content"] = text[:10000]  # Limit content length
        
        # Extract contact info
        page_data["emails"] = self._extract_emails(text)
        page_data["phones"] = self._extract_phones(text)
    
    def _extract_emails(self, text: str) -> List[str]:
        """Extract email addresses from text"""
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        return list(set(re.findall(email_pattern, text)))
    
    def _extract_phones(self, text: str) -> List[str]:
        """Extract UK phone numbers from text with support for multiple formats"""
        # Collection of patterns for UK phone number formats
        uk_phone_patterns = [
            # UK mobile numbers (various formats)
            r'(?:(?:\+44\s?|0)7\d{3}|\(\+44\s?7\d{3}\)|\(0?7\d{3}\))\s?\d{3}\s?\d{3}',
            r'(?:(?:\+44|0)7\d{9})',
            
            # UK landline numbers (various formats)
            r'(?:(?:\+44\s?|0)\d{2,5}|\(\+44\s?\d{2,5}\)|\(0\d{2,5}\))\s?\d{5,8}',
            
            # Common UK area codes with spaces/separators
            r'(?:01[0-9]{2,3}|02[0-9]|0[3-9][0-9])[-.\s]?[0-9]{3,4}[-.\s]?[0-9]{3,4}',
            
            # UK numbers with text indicators nearby
            r'(?:tel|telephone|phone|call|dial|contact|mob|mobile|cell|fax)(?:\s|:|\.|;)+(?:(?:\+44|0)\d[\d\s\-\(\)\.]{7,17}\d)',
            
            # UK numbers with "+" as international prefix
            r'\+44\s?(?:\(0\))?\s?(?:\d[\d\s\-\(\)\.]{7,17}\d)'
        ]
        
        # Combine all patterns
        combined_pattern = '|'.join(f'({pattern})' for pattern in uk_phone_patterns)
        
        # Extract all matches
        matches = re.findall(combined_pattern, text, re.IGNORECASE)
        
        # Flatten the list of tuples that findall returns with our grouped patterns
        phone_numbers = []
        for match_groups in matches:
            # Get the non-empty group from each match
            for group in match_groups:
                if group:
                    # Clean up the phone number
                    cleaned = self._clean_phone_number(group)
                    if cleaned and len(cleaned) >= 10:  # UK numbers are at least 10 digits with leading 0
                        phone_numbers.append(cleaned)
        
        # Remove duplicates
        return list(set(phone_numbers))
    
    def _clean_phone_number(self, phone: str) -> str:
        """Clean and standardise a UK phone number"""
        # Convert to lowercase to handle variations like "Tel: 01234 567890"
        lower_phone = phone.lower()
        
        # Strip out common text prefixes
        prefixes = ['tel', 'telephone', 'phone', 'call', 'dial', 'contact', 'mob', 'mobile', 'cell', 'fax']
        for prefix in prefixes:
            if prefix in lower_phone:
                # Get everything after the prefix and any following punctuation
                phone = re.sub(f'.*{prefix}[^0-9+]*', '', lower_phone, flags=re.IGNORECASE)
                break
        
        # Remove all non-digit characters except + (for international format)
        digits_only = ''.join(c for c in phone if c.isdigit() or c == '+')
        
        # Convert international format to standard UK format if needed
        if digits_only.startswith('+44'):
            digits_only = '0' + digits_only[3:]
        
        return digits_only
    
    def _format_search_data_for_model(self, business_name: str, search_data: Dict) -> str:
        """Format the search results data for the model"""
        formatted_text = f"Find contact information for: {business_name}\n\n"
        formatted_text += "SEARCH RESULTS ANALYSIS:\n\n"
        
        # Add any contact info found directly in search results
        if search_data.get("contact_info_from_search"):
            contact_info = search_data["contact_info_from_search"]
            
            if contact_info.get("phones"):
                formatted_text += f"PHONES FROM SEARCH: {', '.join(contact_info['phones'])}\n"
            
            if contact_info.get("emails"):
                formatted_text += f"EMAILS FROM SEARCH: {', '.join(contact_info['emails'])}\n"
        
        # Add list of URLs found
        formatted_text += "\nFOUND URLS:\n"
        for i, url in enumerate(search_data["urls"]):
            formatted_text += f"{i+1}. {url}\n"
        
        # Add instructions for the model
        formatted_text += "\nINSTRUCTIONS: Extract any contact information visible in the search results. "
        formatted_text += "List all potential sources of information with their URL numbers. "
        formatted_text += "Recommend which URLs the user should explore for more complete information.\n"
        
        return formatted_text
    
    def _format_url_data_for_model(self, business_name: str, url: str, page_data: Dict) -> str:
        """Format a single URL's data for the model"""
        formatted_text = f"Extract detailed contact information for {business_name} from this specific webpage:\n\n"
        formatted_text += f"URL: {url}\n"
        formatted_text += f"TITLE: {page_data['title']}\n\n"
        
        if page_data.get('emails'):
            formatted_text += f"EXTRACTED EMAILS: {', '.join(page_data['emails'])}\n"
        
        if page_data.get('phones'):
            formatted_text += f"EXTRACTED PHONES: {', '.join(page_data['phones'])}\n"
        
        formatted_text += f"CONTENT:\n{page_data.get('text_content', '')}\n\n"
        
        formatted_text += "INSTRUCTIONS: Provide complete contact details found on this page. "
        formatted_text += "Format the information clearly and note the source URL.\n"
        
        return formatted_text