import os
import re
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from perplexipy import PerplexityClient

# Load environment variables from .env file
load_dotenv()

class SearchTools:
    def __init__(self):
        self.perplexity_client = PerplexityClient(os.getenv("PERPLEXITY_API_KEY"))

    def search_internet(self, query: str) -> str:
        """
        A tool to search the internet with a query using Perplexity AI.
        """
        if not self.perplexity_client:
            return "Error: Perplexity API key not found. Please set the PERPLEXITY_API_KEY environment variable."
        
        try:
            result = self.perplexity_client.query(query)
            return result
        except Exception as e:
            return f"An error occurred during the search: {e}"

    def scrape_website_for_contact_info(self, url: str) -> dict:
        """
        Scrapes a website to find contact information like email and social media links.
        """
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # Find email addresses
            emails = re.findall(r'[\w\.-]+@[\w\.-]+', soup.get_text())
            # Filter out common non-contact emails
            emails = [email for email in emails if not email.endswith(('.png', '.jpg', '.jpeg', '.gif'))]
            
            contact_info = {
                "emails": list(set(emails)),
                "url": url
            }
            
            return contact_info

        except requests.exceptions.RequestException as e:
            return {"error": f"Could not retrieve the webpage: {e}"}
        except Exception as e:
            return {"error": f"An error occurred during scraping: {e}"} 