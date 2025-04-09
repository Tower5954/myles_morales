from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import logging
import urllib.parse
import random

class SeleniumScraper:
    """Class for web scraping using Selenium with Chrome webdriver"""
    
    def __init__(self, headless=True, timeout=30):
        """
        Initialise the Selenium scraper with Chrome webdriver
        
        Args:
            headless (bool): Run browser in headless mode
            timeout (int): Default wait timeout for web elements
        """
        # Configure logging
        logging.basicConfig(level=logging.INFO, 
                            format='%(asctime)s - %(levelname)s: %(message)s')
        self.logger = logging.getLogger(__name__)
        
        # Configure Chrome options
        self.options = Options()
        if headless:
            self.options.add_argument("--headless")
        
        # Add more sophisticated anti-detection arguments
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-dev-shm-usage")
        self.options.add_argument("--disable-blink-features=AutomationControlled")
        self.options.add_argument("--disable-extensions")
        self.options.add_argument("--disable-gpu")
        self.options.add_argument("--disable-software-rasterizer")
        
        # Randomize user agent
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"
        ]
        self.options.add_argument(f"user-agent={random.choice(user_agents)}")
        
        # Experimental options to avoid detection
        self.options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.options.add_experimental_option('useAutomationExtension', False)
        
        # Service and driver setup
        self.timeout = timeout
        self.service = Service(ChromeDriverManager().install())
        
        # Create the WebDriver
        self.driver = None
        self._create_driver()
    
    def _create_driver(self):
        """Create a new WebDriver instance"""
        try:
            self.driver = webdriver.Chrome(service=self.service, options=self.options)
            self.driver.set_page_load_timeout(self.timeout)
            
            # Additional stealth techniques
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        except Exception as e:
            self.logger.error(f"Error creating WebDriver: {e}")
            raise
    
    def _handle_consent_popup(self):
        """Handle Google consent popups with multiple strategies"""
        consent_strategies = [
            # Different ways to locate and click consent buttons
            {"method": By.XPATH, "selector": "//button[contains(., 'Accept all')]"},
            {"method": By.XPATH, "selector": "//button[contains(., 'I agree')]"},
            {"method": By.ID, "selector": "L2AGLb"},
            {"method": By.XPATH, "selector": "//div[@role='dialog']//button"},
            {"method": By.CSS_SELECTOR, "selector": "button[aria-label='Accept all']"}
        ]
        
        for strategy in consent_strategies:
            try:
                # Switch method based on selector type
                find_method = strategy['method']
                selector = strategy['selector']
                
                # Wait and try to click
                consent_button = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((find_method, selector))
                )
                consent_button.click()
                
                self.logger.info(f"Clicked consent button with {find_method}: {selector}")
                time.sleep(random.uniform(1.5, 3.5))  # Random delay
                return True
            except Exception as e:
                self.logger.debug(f"Failed with {strategy}: {e}")
        
        self.logger.warning("No consent button found or couldn't click it")
        return False
    
    def search(self, query, max_results=10):
        """
        Perform a Google search and return result URLs
        
        Args:
            query (str): Search query
            max_results (int): Maximum number of results to return
        
        Returns:
            list: URLs of search results
        """
        # Prepare search query variations
        search_queries = [
            query,
            f"{query} business contact",
            f"{query} website"
        ]
        
        result_urls = []
        
        # Try multiple search queries
        for search_query in search_queries:
            if result_urls and len(result_urls) >= max_results:
                break
            
            # Encode the query for URL
            encoded_query = urllib.parse.quote(search_query)
            search_url = f"https://www.google.com/search?q={encoded_query}"
            
            try:
                # Reload driver if previous session was closed
                if self.driver is None:
                    self._create_driver()
                
                self.logger.info(f"Searching Google with query: {search_query}")
                self.driver.get(search_url)
                
                # Random delay to mimic human behavior
                time.sleep(random.uniform(2.5, 5.5))
                
                # Handle consent popup
                self._handle_consent_popup()
                
                # Search result locators with multiple strategies
                search_result_locators = [
                    {"method": By.CSS_SELECTOR, "selector": "div.g a[href^='http']"},
                    {"method": By.XPATH, "selector": "//div[contains(@class, 'yuRUbf')]//a"},
                    {"method": By.XPATH, "selector": "//a[@href and starts-with(@href, 'http') and not(contains(@href, 'google'))]"}
                ]
                
                # Try different locators
                for locator in search_result_locators:
                    try:
                        # Find links
                        links = self.driver.find_elements(locator['method'], locator['selector'])
                        self.logger.info(f"Found {len(links)} search result links using {locator}")
                        
                        # Process links
                        for link in links:
                            try:
                                href = link.get_attribute("href")
                                
                                # Validate URL
                                if href and href.startswith("http"):
                                    # Skip irrelevant domains
                                    irrelevant_domains = [
                                        'google.com', 'youtube.com', 
                                        'facebook.com', 'twitter.com'
                                    ]
                                    
                                    if not any(domain in href for domain in irrelevant_domains):
                                        # Avoid duplicates
                                        if href not in result_urls:
                                            result_urls.append(href)
                                            self.logger.info(f"Added result URL: {href}")
                                            
                                            if len(result_urls) >= max_results:
                                                break
                            except Exception as link_err:
                                self.logger.warning(f"Error processing link: {link_err}")
                        
                        # If we found results, break the locator loop
                        if result_urls:
                            break
                    
                    except Exception as locator_err:
                        self.logger.warning(f"Error with locator {locator}: {locator_err}")
            
            except Exception as search_err:
                self.logger.error(f"Search error for query {search_query}: {search_err}")
        
        self.logger.info(f"Final result URLs count: {len(result_urls)}")
        return result_urls
    
    def scrape_url(self, url):
        """
        Scrape a specific URL and return its content
        
        Args:
            url (str): URL to scrape
        
        Returns:
            dict: Scraped page information
        """
        self.logger.info(f"Scraping URL with Selenium: {url}")
        
        try:
            # Reload driver if previous session was closed
            if self.driver is None:
                self._create_driver()
            
            self.driver.get(url)
            time.sleep(random.uniform(2.5, 5.5))  # Random delay to mimic human behavior
            
            # Get page content
            content = self.driver.page_source
            title = self.driver.title
            
            return {
                "url": url,
                "title": title,
                "content": content,
            }
        except Exception as e:
            self.logger.error(f"Error scraping URL {url}: {e}")
            return {
                "url": url,
                "error": str(e),
                "content": ""
            }
    
    def close(self):
        """Close the browser"""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
            self.logger.info("Browser closed successfully")
        except Exception as e:
            self.logger.error(f"Error closing browser: {e}")