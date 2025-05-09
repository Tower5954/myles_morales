# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from webdriver_manager.chrome import ChromeDriverManager
# import time
# import logging
# import urllib.parse
# import random

# class SeleniumScraper:
#     """Class for web scraping using Selenium with Chrome webdriver"""
    
#     def __init__(self, headless=True, timeout=30):
#         """
#         Initialise the Selenium scraper with Chrome webdriver
        
#         Args:
#             headless (bool): Run browser in headless mode
#             timeout (int): Default wait timeout for web elements
#         """
#         # Configure logging
#         logging.basicConfig(level=logging.INFO, 
#                             format='%(asctime)s - %(levelname)s: %(message)s')
#         self.logger = logging.getLogger(__name__)
        
#         # Configure Chrome options
#         self.options = Options()
#         if headless:
#             self.options.add_argument("--headless")
        
#         # Add more sophisticated anti-detection arguments
#         self.options.add_argument("--no-sandbox")
#         self.options.add_argument("--disable-dev-shm-usage")
#         self.options.add_argument("--disable-blink-features=AutomationControlled")
#         self.options.add_argument("--disable-extensions")
#         self.options.add_argument("--disable-gpu")
#         self.options.add_argument("--disable-software-rasterizer")
        
#         # Randomize user agent
#         user_agents = [
#             "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
#             "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
#             "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"
#         ]
#         self.options.add_argument(f"user-agent={random.choice(user_agents)}")
        
#         # Experimental options to avoid detection
#         self.options.add_experimental_option("excludeSwitches", ["enable-automation"])
#         self.options.add_experimental_option('useAutomationExtension', False)
        
#         # Service and driver setup
#         self.timeout = timeout
#         self.service = Service(ChromeDriverManager().install())
        
#         # Create the WebDriver
#         self.driver = None
#         self._create_driver()
    
#     def _create_driver(self):
#         """Create a new WebDriver instance"""
#         try:
#             self.driver = webdriver.Chrome(service=self.service, options=self.options)
#             self.driver.set_page_load_timeout(self.timeout)
            
#             # Additional stealth techniques
#             self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
#         except Exception as e:
#             self.logger.error(f"Error creating WebDriver: {e}")
#             raise
    
#     def _handle_consent_popup(self):
#         """Handle Google consent popups with multiple strategies"""
#         consent_strategies = [
#             # Different ways to locate and click consent buttons
#             {"method": By.XPATH, "selector": "//button[contains(., 'Accept all')]"},
#             {"method": By.XPATH, "selector": "//button[contains(., 'I agree')]"},
#             {"method": By.ID, "selector": "L2AGLb"},
#             {"method": By.XPATH, "selector": "//div[@role='dialog']//button"},
#             {"method": By.CSS_SELECTOR, "selector": "button[aria-label='Accept all']"}
#         ]
        
#         for strategy in consent_strategies:
#             try:
#                 # Switch method based on selector type
#                 find_method = strategy['method']
#                 selector = strategy['selector']
                
#                 # Wait and try to click
#                 consent_button = WebDriverWait(self.driver, 5).until(
#                     EC.element_to_be_clickable((find_method, selector))
#                 )
#                 consent_button.click()
                
#                 self.logger.info(f"Clicked consent button with {find_method}: {selector}")
#                 time.sleep(random.uniform(1.5, 3.5))  # Random delay
#                 return True
#             except Exception as e:
#                 self.logger.debug(f"Failed with {strategy}: {e}")
        
#         self.logger.warning("No consent button found or couldn't click it")
#         return False
    
#     def search(self, query, max_results=10):
#         """
#         Perform a Google search and return result URLs
        
#         Args:
#             query (str): Search query
#             max_results (int): Maximum number of results to return
        
#         Returns:
#             list: URLs of search results
#         """
#         # Prepare search query variations
#         search_queries = [
#             query,
#             f"{query} business contact",
#             f"{query} website"
#         ]
        
#         result_urls = []
        
#         # Try multiple search queries
#         for search_query in search_queries:
#             if result_urls and len(result_urls) >= max_results:
#                 break
            
#             # Encode the query for URL
#             encoded_query = urllib.parse.quote(search_query)
#             search_url = f"https://www.google.com/search?q={encoded_query}"
            
#             try:
#                 # Reload driver if previous session was closed
#                 if self.driver is None:
#                     self._create_driver()
                
#                 self.logger.info(f"Searching Google with query: {search_query}")
#                 self.driver.get(search_url)
                
#                 # Random delay to mimic human behavior
#                 time.sleep(random.uniform(2.5, 5.5))
                
#                 # Handle consent popup
#                 self._handle_consent_popup()
                
#                 # Search result locators with multiple strategies
#                 search_result_locators = [
#                     {"method": By.CSS_SELECTOR, "selector": "div.g a[href^='http']"},
#                     {"method": By.XPATH, "selector": "//div[contains(@class, 'yuRUbf')]//a"},
#                     {"method": By.XPATH, "selector": "//a[@href and starts-with(@href, 'http') and not(contains(@href, 'google'))]"}
#                 ]
                
#                 # Try different locators
#                 for locator in search_result_locators:
#                     try:
#                         # Find links
#                         links = self.driver.find_elements(locator['method'], locator['selector'])
#                         self.logger.info(f"Found {len(links)} search result links using {locator}")
                        
#                         # Process links
#                         for link in links:
#                             try:
#                                 href = link.get_attribute("href")
                                
#                                 # Validate URL
#                                 if href and href.startswith("http"):
#                                     # Skip irrelevant domains
#                                     irrelevant_domains = [
#                                         'google.com', 'youtube.com', 
#                                         'facebook.com', 'twitter.com'
#                                     ]
                                    
#                                     if not any(domain in href for domain in irrelevant_domains):
#                                         # Avoid duplicates
#                                         if href not in result_urls:
#                                             result_urls.append(href)
#                                             self.logger.info(f"Added result URL: {href}")
                                            
#                                             if len(result_urls) >= max_results:
#                                                 break
#                             except Exception as link_err:
#                                 self.logger.warning(f"Error processing link: {link_err}")
                        
#                         # If we found results, break the locator loop
#                         if result_urls:
#                             break
                    
#                     except Exception as locator_err:
#                         self.logger.warning(f"Error with locator {locator}: {locator_err}")
            
#             except Exception as search_err:
#                 self.logger.error(f"Search error for query {search_query}: {search_err}")
        
#         self.logger.info(f"Final result URLs count: {len(result_urls)}")
#         return result_urls
    
#     def scrape_url(self, url):
#         """
#         Scrape a specific URL and return its content
        
#         Args:
#             url (str): URL to scrape
        
#         Returns:
#             dict: Scraped page information
#         """
#         self.logger.info(f"Scraping URL with Selenium: {url}")
        
#         try:
#             # Reload driver if previous session was closed
#             if self.driver is None:
#                 self._create_driver()
            
#             self.driver.get(url)
#             time.sleep(random.uniform(2.5, 5.5))  # Random delay to mimic human behavior
            
#             # Get page content
#             content = self.driver.page_source
#             title = self.driver.title
            
#             return {
#                 "url": url,
#                 "title": title,
#                 "content": content,
#             }
#         except Exception as e:
#             self.logger.error(f"Error scraping URL {url}: {e}")
#             return {
#                 "url": url,
#                 "error": str(e),
#                 "content": ""
#             }
    
#     def close(self):
#         """Close the browser"""
#         try:
#             if self.driver:
#                 self.driver.quit()
#                 self.driver = None
#             self.logger.info("Browser closed successfully")
#         except Exception as e:
#             self.logger.error(f"Error closing browser: {e}")

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
from bs4 import BeautifulSoup

class SeleniumScraper:
    """Selenium-based scraper with improved error handling"""
    
    def __init__(self, headless=True, timeout=30):
        # Configure Chrome options
        self.options = Options()
        if headless:
            self.options.add_argument("--headless")
        
        # Basic anti-detection settings
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument("--disable-blink-features=AutomationControlled")
        self.options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.options.add_experimental_option('useAutomationExtension', False)
        
        # Set a common user agent
        self.options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        
        # Setup
        self.timeout = timeout
        self.service = Service(ChromeDriverManager().install())
        self.driver = None
    
    def _create_driver(self):
        """Create a new WebDriver instance"""
        if not self.driver:
            try:
                self.driver = webdriver.Chrome(service=self.service, options=self.options)
                self.driver.set_page_load_timeout(self.timeout)
                
                # Set window size to a normal desktop size
                self.driver.set_window_size(1366, 768)
                
                # Additional anti-detection
                self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                print("WebDriver created successfully")
            except Exception as e:
                print(f"Error creating WebDriver: {e}")
                raise
    
    def _handle_cookies_popup(self):
        """Attempt to handle common cookie consent popups"""
        try:
            # Common cookie button patterns
            cookie_button_patterns = [
                {"by": By.XPATH, "value": "//button[contains(text(), 'Accept') or contains(text(), 'accept') or contains(text(), 'Allow')]"},
                {"by": By.XPATH, "value": "//button[contains(@class, 'cookie') or contains(@id, 'cookie')]"},
                {"by": By.XPATH, "value": "//a[contains(text(), 'Accept') or contains(text(), 'accept')]"},
                {"by": By.ID, "value": "onetrust-accept-btn-handler"},
                {"by": By.ID, "value": "accept-cookies"},
                {"by": By.ID, "value": "cookie-accept"}
            ]
            
            for pattern in cookie_button_patterns:
                try:
                    # Wait a short time for the specific pattern
                    button = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((pattern["by"], pattern["value"]))
                    )
                    button.click()
                    print(f"Clicked cookie button with {pattern}")
                    time.sleep(1)
                    return True
                except:
                    continue
            
            return False
        except:
            return False
    
    def search(self, query, max_results=5):
        """
        Perform a search with improved error handling and better filtering
        of irrelevant domains and search engine results
        """
        # Prepare multiple search engines in case one fails
        search_engines = [
            f"https://www.google.com/search?q={query.replace(' ', '+')}",
        ]
        
        result_urls = []
        # Track URLs we've already seen to prevent duplicates
        seen_urls = set()
        
        for search_url in search_engines:
            if len(result_urls) >= max_results:
                break  # If we already have enough results, don't try other engines
                
            try:
                print(f"Searching with URL: {search_url}")
                self._create_driver()
                self.driver.get(search_url)
                time.sleep(3)  # Wait for page to load
                
                # Handle cookies banner if present
                self._handle_cookies_popup()
                
                # Wait for search results to load
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "a"))
                )
                
                # Find all links
                links = self.driver.find_elements(By.TAG_NAME, 'a')
                print(f"Found {len(links)} links on search page")
                
                # Comprehensive list of domains to exclude
                excluded_domains = [
                    'google.com', 'google.co.uk', 'gstatic.com', 'googleapis.com',
                    'bing.com', 'microsoft.com', 'msn.com', 'live.com',
                    'youtube.com', 'facebook.com', 'twitter.com', 'instagram.com',
                    'linkedin.com', 'pinterest.com', 'reddit.com', 'amazon.com',
                    'wikipedia.org', 'wikimedia.org', 'apple.com', 'github.com',
                    'adobe.com', 'netflix.com'
                ]
                
                # Extract result URLs with better filtering
                for link in links:
                    try:
                        href = link.get_attribute("href")
                        
                        # Skip URLs we've already processed
                        if href in seen_urls:
                            continue
                        
                        # Process and filter URLs
                        if href and href.startswith('http'):
                            # Extract the base domain for duplicate checking
                            base_domain = None
                            if '://' in href:
                                try:
                                    domain_part = href.split('://', 1)[1].split('/', 1)[0]
                                    base_domain = '.'.join(domain_part.split('.')[-2:])
                                except IndexError:
                                    pass
                            
                            # Skip URLs with specific patterns or from excluded domains
                            if (not any(domain in href.lower() for domain in excluded_domains) and
                                not any(pattern in href for pattern in ['/search?', '/intl/', '/accounts/', '/policies/', '/preferences'])):
                                
                                # Skip if we already have a URL from this domain
                                domain_exists = False
                                if base_domain:
                                    domain_exists = any(base_domain in existing_url for existing_url in result_urls)
                                
                                # Only add if we don't already have this domain, unless it's a contact page
                                if 'contact' in href.lower() or not domain_exists:
                                    # Mark as seen
                                    seen_urls.add(href)
                                    
                                    # Prioritize contact pages
                                    if 'contact' in href.lower():
                                        result_urls.insert(0, href)
                                        print(f"Added priority result URL: {href}")
                                    else:
                                        result_urls.append(href)
                                        print(f"Added result URL: {href}")
                                    
                                    if len(result_urls) >= max_results:
                                        break
                    except Exception as link_err:
                        print(f"Error processing link: {link_err}")
                        continue
                
            except Exception as e:
                print(f"Search error with {search_url}: {e}")
        
        # If we found URLs, make sure contact pages are prioritized
        if result_urls:
            # Remove duplicates while preserving order
            unique_results = []
            seen = set()
            for url in result_urls:
                base_url = url.split('#')[0].split('?')[0]  # Remove fragments and query params
                
                # Skip duplicates of the same base URL
                if base_url in seen:
                    continue
                seen.add(base_url)
                unique_results.append(url)
            
            result_urls = unique_results
            
            # Re-sort URLs to prioritize contact pages and the target domain
            contact_urls = []
            target_domain_urls = []
            other_urls = []
            
            target_parts = [part.lower() for part in query.split() if '.' in part]
            
            for url in result_urls:
                if '/contact' in url.lower():
                    contact_urls.append(url)
                elif any(part in url.lower() for part in target_parts):
                    target_domain_urls.append(url)
                else:
                    other_urls.append(url)
            
            # Rebuild the results list in priority order
            result_urls = contact_urls + target_domain_urls + other_urls
            
            # Limit to max_results
            result_urls = result_urls[:max_results]
        else:
            print("WARNING: Could not get any search results")
            
            # Try directly accessing the website if it's in the query
            website_hints = [x for x in query.split() if '.com' in x or '.org' in x or '.co.uk' in x or '.nhs.uk' in x]
            for hint in website_hints:
                if not hint.startswith('http'):
                    hint = 'https://' + hint
                result_urls.append(hint)
                print(f"Added direct website URL from query: {hint}")
        
        return result_urls
    
    def scrape_url(self, url):
        """
        Scrape a URL with extensive error handling and content extraction
        """
        try:
            print(f"Scraping URL: {url}")
            self._create_driver()
            
            # Set page load timeout
            self.driver.set_page_load_timeout(20)
            
            # Load the URL
            self.driver.get(url)
            
            # Wait for page to load content
            print("Waiting for page to load...")
            time.sleep(5)  # Initial wait
            
            # Handle cookies banner if present
            self._handle_cookies_popup()
            
            # Wait for the body to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Get title
            title = self.driver.title
            print(f"Page title: {title}")
            
            # Get page source after JavaScript execution
            page_source = self.driver.page_source
            
            # Use BeautifulSoup to extract text
            soup = BeautifulSoup(page_source, "html.parser")
            
            # Special handling for contact pages
            contact_text = ""
            
            # Look for contact-specific sections first
            contact_elements = soup.find_all(['div', 'section'], class_=lambda c: c and ('contact' in c.lower() or 'address' in c.lower()))
            if contact_elements:
                for element in contact_elements:
                    contact_text += element.get_text(separator="\n", strip=True) + "\n\n"
            
            # Also look for address and phone elements
            address_elements = soup.find_all(['address', 'div'], class_=lambda c: c and 'address' in c.lower())
            if address_elements:
                for element in address_elements:
                    contact_text += "ADDRESS SECTION:\n" + element.get_text(separator="\n", strip=True) + "\n\n"
            
            # Look for footer which often contains contact info
            footer_elements = soup.find_all(['footer', 'div'], class_=lambda c: c and 'footer' in c.lower())
            if footer_elements:
                for element in footer_elements:
                    contact_text += "FOOTER SECTION:\n" + element.get_text(separator="\n", strip=True) + "\n\n"
            
            # Remove script and style elements from the main soup
            for script in soup(["script", "style"]):
                script.extract()
            
            # Get the general text content
            general_text = soup.get_text(separator="\n", strip=True)
            
            # Combine the targeted contact sections with the general text
            if contact_text:
                text = "CONTACT SECTIONS:\n" + contact_text + "\n\nFULL PAGE TEXT:\n" + general_text
            else:
                text = general_text
            
            # If we have almost no text, try direct Selenium extraction
            if len(text.strip()) < 100:
                print("Warning: Very little text extracted. Trying direct Selenium extraction.")
                text = self.driver.find_element(By.TAG_NAME, "body").text
            
            return {
                "url": url,
                "title": title,
                "content": text  # Return the full text content
            }
        except Exception as e:
            print(f"Error scraping URL {url}: {e}")
            import traceback
            traceback.print_exc()
            return {
                "url": url,
                "error": str(e),
                "content": "Error: Could not retrieve content from this website."
            }
    
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
            self.driver = None
            print("Browser closed")