from lib.base_joblisting import JobListing
from lib.base_scraper import JobScraper
from typing import List, Dict, Any
import requests
import logging

# -------------------------------
# Job Listing Class
# -------------------------------
class QRTJobListing(JobListing):
    def __init__(self, listing_id: str, title: str, location: str):
        self.id = listing_id
        self.title = title
        self.location = location
        self.link = f"https://www.qube-rt.com/careers/job?gh_jid={listing_id}"

    def get_id(self):
        return self.id

    def generate_telegram_message(self):
        return f"{self.title}\nLocation: {self.location}\n[Link]({self.link})"

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "location": self.location,
            "link": self.link
        }

# -------------------------------
# Scraper Class
# -------------------------------
class QRTJobScraper(JobScraper):
    def __init__(self):
        super().__init__(company_name="Qube Research & Technologies")
        self.logo_path = "lib/qrt.png"
        self.url = "https://boards-api.greenhouse.io/v1/boards/quberesearchandtechnologies/jobs"

    def scrape(self):
        try:
            response = requests.get(self.url).json()
            jobs_on_board = response.get("jobs", [])
        except Exception as e:
            logging.error(f"Unable to fetch job listings: {e}")
            return []

        # Filter only jobs in Zurich
        zurich_jobs = [
            job for job in jobs_on_board
            if "zurich" in job.get("location", {}).get("name", "").lower()
        ]

        self.current_listings.extend([
            QRTJobListing(
                listing_id=job["id"],
                title=job["title"],
                location=job.get("location", {}).get("name", "N/A")
            )
            for job in zurich_jobs
        ])

        return self.current_listings

    def _create_listing_from_dict(self, data: Dict[str, Any]) -> QRTJobListing:
        return QRTJobListing(
            listing_id=data["id"],
            title=data["title"],
            location=data.get("location", "N/A")
        )

# -------------------------------
# Quick test
# -------------------------------
if __name__ == "__main__":
    scraper = QRTJobScraper()
    jobs = scraper.scrape()
    print(f"Found {len(jobs)} jobs in Zurich")
    for job in jobs:
        print(job.generate_telegram_message())
