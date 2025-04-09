import time
import requests
import re
from typing import Dict, List, Any
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from config_manager import ConfigManager

class WebScraper:
    """Handles web scraping functionality"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config = config_manager
        self.headers = {
            "User-Agent": self.config.get("user_agent")
        }
        self.timeout = self.config.get("request_timeout")
        self.delay = self.config.get("request_delay")
    
    def search(self, query: str) -> List[str]:
        """Perform a search and return result URLs"""
        search_url = f"{self.config.get('search_engine')}{query.replace(' ', '+')}"
        max_results = self.config.get("max_search_results")
        print(f"Searching URL: {search_url}")
        
        # Update headers to mimic a browser better
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        
        try:
            print(f"Sending request to search engine...")
            response = requests.get(search_url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            print(f"Got response with status code: {response.status_code}")
            
            # Store the search response for later extraction
            self.last_search_response = response.text
            
            # Save the response for debugging
            with open("search_response.html", "w", encoding="utf-8") as f:
                f.write(response.text)
            print(f"Saved search response to search_response.html")
            
            # Parse the search results page
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Extract ALL links from the page
            all_links = soup.find_all('a')
            print(f"Found {len(all_links)} total links on the page")
            
            # Extract result URLs
            result_urls = []
            for link in all_links:
                href = link.get('href')
                if href and href.startswith('http'):
                    # Skip search engine domains and common non-result links
                    if not any(domain in href for domain in [
                        'bing.com', 'google.com', 'youtube.com', 'microsoft.com', 
                        'login', 'signin', 'account', 'help', 'support'
                    ]):
                        result_urls.append(href)
                        print(f"Added result URL: {href}")
                        if len(result_urls) >= max_results:
                            break
            
            print(f"Final result URLs count: {len(result_urls)}")
            return result_urls
        except Exception as e:
            print(f"Error performing search: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    def extract_search_page_info(self) -> Dict[str, List[str]]:
        """Extract any contact information directly from the search results page"""
        if not self.last_search_response:
            return {"phones": [], "emails": []}
        
        # Parse the search page content
        soup = BeautifulSoup(self.last_search_response, "html.parser")
        
        # Extract text content from the search page
        for script in soup(["script", "style"]):
            script.extract()
        
        text = soup.get_text(separator="\n", strip=True)
        
        # Extract contact info using our existing methods
        emails = self._extract_emails(text)
        phones = self._extract_phones(text)
        
        return {
            "emails": emails,
            "phones": phones
        }
    
    def scrape_url(self, url: str) -> Dict[str, Any]:
        """Scrape a single URL and return its content"""
        try:
            # Add delay to be respectful to websites
            time.sleep(self.delay)
            
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            
            # Get the page content
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Extract relevant information
            title = soup.title.string if soup.title else "No title"
            
            # Extract text content
            for script in soup(["script", "style"]):
                script.extract()
            
            text = soup.get_text(separator="\n", strip=True)
            
            # Extract potential contact information
            emails = self._extract_emails(text)
            phones = self._extract_phones(text)
            
            # Extract links for further processing
            links = []
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                if href and not href.startswith(('#', 'javascript:')):
                    # Convert relative URLs to absolute
                    absolute_url = urljoin(url, href)
                    links.append(absolute_url)
            
            return {
                "url": url,
                "title": title,
                "content": text[:5000],  # Limit content length
                "emails": emails,
                "phones": phones,
                "links": links[:20]  # Limit number of links
            }
        except Exception as e:
            print(f"Error scraping URL {url}: {str(e)}")
            return {
                "url": url,
                "error": str(e),
                "content": "",
                "emails": [],
                "phones": [],
                "links": []
            }
    
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
        """Clean and standardize a UK phone number"""
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
        
        # Format for readability (optional)
        # Could add formatting like: 07xxx xxx xxx or 01xxx xxxxxx
        
        return digits_only