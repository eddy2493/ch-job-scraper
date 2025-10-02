from lib.base_joblisting import JobListing
from lib.base_scraper import JobScraper
from typing import List, Dict, Any
import requests
import logging


class IBMJobListing(JobListing):
    def __init__(self, listing_id: str, title: str, category: str, work_type: str, link: str):
        self.id = listing_id
        self.title = title
        self.category = category
        self.work_type = work_type
        self.link = link
        self.company = "IBM"

    def get_id(self) -> str:
        return self.id

    def generate_telegram_message(self) -> str:
        work_info = f" ({self.work_type})" if self.work_type else ""
        return f"*{self.title}*{work_info}\n{self.category}\n[Link]({self.link})"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "category": self.category,
            "work_type": self.work_type,
            "link": self.link
        }


class IBMJobScraper(JobScraper):
    def __init__(self):
        super().__init__(company_name="IBM")
        self.api_url = "https://www-api.ibm.com/search/api/v2"
        self.location = "Switzerland"
        self.logo_path = "lib/IBM.png"

    def scrape(self) -> List[IBMJobListing]:
        """Scrape IT-related job listings from IBM Switzerland using their search API."""
        listings = []

        headers = {
            'accept': 'application/json, text/plain, */*',
            'content-type': 'application/json',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
        }

        json_data = {
            'appId': 'careers',
            'scopes': ['careers2'],
            'query': {'bool': {'must': []}},
            'post_filter': {'term': {'field_keyword_05': self.location}},
            'size': 100,
            '_source': ['_id', 'title', 'url', 'field_keyword_08', 'field_keyword_17'],
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=json_data)

            if response.status_code != 200:
                logging.error(f"IBM API returned {response.status_code}")
                return listings

            data = response.json()
            jobs = data.get('hits', {}).get('hits', [])

            # IT-related keywords
            it_keywords = ['software', 'engineer', 'developer', 'data', 'cloud',
                          'it', 'technical', 'architect', 'devops', 'security',
                          'infrastructure', 'systems', 'technology', 'platform',
                          'automation', 'backend', 'frontend', 'fullstack']

            for job in jobs:
                source = job.get('_source', {})
                job_id = job.get('_id', '')
                title = source.get('title', '')
                category = source.get('field_keyword_08', 'Technology')
                work_type = source.get('field_keyword_17', '')
                url = source.get('url', '')

                # Filter for IT-related jobs
                if (any(kw in title.lower() for kw in it_keywords) or
                    'software' in category.lower() or
                    'engineering' in category.lower() or
                    'infrastructure' in category.lower() or
                    'technology' in category.lower() or
                    'data' in category.lower()):

                    listing = IBMJobListing(
                        listing_id=job_id,
                        title=title,
                        category=category,
                        work_type=work_type,
                        link=url
                    )
                    listings.append(listing)

            self.current_listings = listings

        except Exception as e:
            logging.error(f"Error scraping IBM jobs: {e}")

        return listings

    def _create_listing_from_dict(self, data: Dict[str, Any]) -> IBMJobListing:
        """Convert a dictionary back into an IBMJobListing object."""
        return IBMJobListing(
            listing_id=data["id"],
            title=data["title"],
            category=data["category"],
            work_type=data["work_type"],
            link=data["link"]
        )