from lib.base_joblisting import JobListing
from lib.base_scraper import JobScraper
from typing import List, Dict, Any
import requests
import logging


class GetYourGuideJobListing(JobListing):
    def __init__(self, listing_id: str, title: str, team: str, location: str, link: str):
        self.id = listing_id
        self.title = title
        self.team = team
        self.location = location
        self.link = link
        self.company = "GetYourGuide"

    def get_id(self) -> str:
        return self.id

    def generate_telegram_message(self) -> str:
        return f"*{self.title}* - {self.team}\n{self.location}\n[Link]({self.link})"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "team": self.team,
            "location": self.location,
            "link": self.link
        }


class GetYourGuideJobScraper(JobScraper):
    def __init__(self):
        super().__init__(company_name="GetYourGuide")
        # GetYourGuide uses Greenhouse API
        self.api_url = "https://boards-api.greenhouse.io/v1/boards/getyourguide/jobs"
        self.location = "Zurich"
        self.logo_path = "lib/getyourguide.png"

    def scrape(self) -> List[GetYourGuideJobListing]:
        """Scrape job listings from GetYourGuide's Greenhouse API."""
        listings = []

        try:
            response = requests.get(self.api_url)
            if response.status_code != 200:
                logging.error(f"Error fetching jobs: {response.status_code}")
                return listings

            data = response.json()

            # Filter for Zurich jobs
            for job in data.get("jobs", []):
                location_name = job.get("location", {}).get("name", "")
                if self.location in location_name:
                    # Get department/team if available
                    departments = job.get("departments", [])
                    team = departments[0]["name"] if departments else "Engineering"

                    # Extract job ID from the URL or use internal_job_id
                    job_id = str(job.get("id", ""))

                    listing = GetYourGuideJobListing(
                        listing_id=job_id,
                        title=job.get("title", ""),
                        team=team,
                        location=location_name,
                        link=job.get("absolute_url", "")
                    )
                    listings.append(listing)

            self.current_listings = listings

        except Exception as e:
            logging.error(f"Error scraping GetYourGuide jobs: {e}")

        return listings

    def _create_listing_from_dict(self, data: Dict[str, Any]) -> GetYourGuideJobListing:
        """Convert a dictionary back into a GetYourGuideJobListing object."""
        return GetYourGuideJobListing(
            listing_id=data["id"],
            title=data["title"],
            team=data["team"],
            location=data["location"],
            link=data["link"]
        )