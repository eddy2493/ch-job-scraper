from lib.base_joblisting import JobListing
from lib.base_scraper import JobScraper
from typing import List, Dict, Any
import requests
import logging


class SBBJobListing(JobListing):
    def __init__(self, listing_id: str, title: str, location: str, link: str):
        self.id = listing_id
        self.title = title
        self.location = location
        self.link = link
        self.company = "SBB"

    def get_id(self) -> str:
        return self.id

    def generate_telegram_message(self) -> str:
        return f"*{self.title}*\n{self.location}\n[Link]({self.link})"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "location": self.location,
            "link": self.link
        }


class SBBJobScraper(JobScraper):
    def __init__(self):
        super().__init__(company_name="SBB")
        self.api_url = "https://company.sbb.ch/content/internet/corporate/de/jobs-karriere/offene-stellen/job-suche/jcr:content/parmain/jobfilter.results.json"
        self.topic = "IT / Telekommunikation"
        self.logo_path = "lib/sbb.png"

    def scrape(self) -> List[SBBJobListing]:
        """Scrape IT/Telekommunikation job listings from SBB."""
        listings = []

        headers = {
            'Accept': '*/*',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
            'X-Requested-With': 'XMLHttpRequest',
        }

        try:
            response = requests.get(self.api_url, headers=headers)

            if response.status_code != 200:
                logging.error(f"SBB API returned {response.status_code}")
                return listings

            data = response.json()

            # Filter for IT / Telekommunikation jobs
            # Attribute "20" contains the topic/category
            for job in data:
                topics = job.get('attributes', {}).get('20', [])

                if self.topic in topics:
                    job_id = job.get('id', '')
                    title = job.get('title', '')

                    # Attribute "100" contains location
                    locations = job.get('attributes', {}).get('100', [])
                    location = ', '.join(locations) if locations else 'Switzerland'

                    link = job.get('links', {}).get('directlink', '')

                    listing = SBBJobListing(
                        listing_id=job_id,
                        title=title,
                        location=location,
                        link=link
                    )
                    listings.append(listing)

            self.current_listings = listings

        except Exception as e:
            logging.error(f"Error scraping SBB jobs: {e}")

        return listings

    def _create_listing_from_dict(self, data: Dict[str, Any]) -> SBBJobListing:
        """Convert a dictionary back into an SBBJobListing object."""
        return SBBJobListing(
            listing_id=data["id"],
            title=data["title"],
            location=data["location"],
            link=data["link"]
        )
