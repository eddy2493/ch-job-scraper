from lib.base_joblisting import JobListing
from lib.base_scraper import JobScraper
from typing import List, Dict, Any
import requests
import logging


class IMCJobListing(JobListing):
    def __init__(self, listing_id: str, title: str, location: str, department: str, link: str):
        self.id = listing_id
        self.title = title
        self.location = location
        self.department = department
        self.link = link
        self.company = "IMC"

    def get_id(self) -> str:
        return self.id

    def generate_telegram_message(self) -> str:
        dept_info = f" - {self.department}" if self.department else ""
        return f"*{self.title}*{dept_info}\n{self.location}\n[Link]({self.link})"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "location": self.location,
            "department": self.department,
            "link": self.link
        }


class IMCJobScraper(JobScraper):
    def __init__(self):
        super().__init__(company_name="IMC")
        self.api_url = "https://boards-api.greenhouse.io/v1/boards/imc/jobs"
        self.location = "Switzerland"
        self.logo_path = "lib/imc.png"

    def scrape(self) -> List[IMCJobListing]:
        """Scrape all job listings from IMC in Switzerland using Greenhouse API."""
        listings = []

        try:
            response = requests.get(self.api_url)

            if response.status_code != 200:
                logging.error(f"IMC Greenhouse API returned {response.status_code}")
                return listings

            data = response.json()
            jobs = data.get('jobs', [])

            for job in jobs:
                location_name = job.get('location', {}).get('name', '')

                # Filter for Switzerland
                if self.location in location_name:
                    job_id = str(job.get('id', ''))
                    title = job.get('title', '')

                    # Get department if available
                    departments = job.get('departments', [])
                    department = departments[0]['name'] if departments else ''

                    listing = IMCJobListing(
                        listing_id=job_id,
                        title=title,
                        location=location_name,
                        department=department,
                        link=job.get('absolute_url', '')
                    )
                    listings.append(listing)

            self.current_listings = listings

        except Exception as e:
            logging.error(f"Error scraping IMC jobs: {e}")

        return listings

    def _create_listing_from_dict(self, data: Dict[str, Any]) -> IMCJobListing:
        """Convert a dictionary back into an IMCJobListing object."""
        return IMCJobListing(
            listing_id=data["id"],
            title=data["title"],
            location=data["location"],
            department=data["department"],
            link=data["link"]
        )
