from lib.base_joblisting import JobListing
from lib.base_scraper import JobScraper
from typing import List, Dict, Any
import requests
import logging

# -------------------------------
# Job Listing Class
# -------------------------------
class MetGroupJobListing(JobListing):
    def __init__(self, listing_id: str, title: str, profession: str, location: str, link: str):
        self.id = listing_id
        self.title = title
        self.profession = profession
        self.location = location
        self.link = link

    def get_id(self):
        return self.id

    def generate_telegram_message(self):
        return f"{self.title} ({self.profession})\nLocation: {self.location}\n[Link]({self.link})"

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "profession": self.profession,
            "location": self.location,
            "link": self.link
        }

# -------------------------------
# Scraper Class
# -------------------------------
class METJobScraper(JobScraper):
    def __init__(self):
        super().__init__(company_name="MET Group")
        self.logo_path = "lib/metgroup.png"
        self.url = "https://api.smartrecruiters.com/v1/companies/metgroup/postings"
        self.params = {
            "limit": "100",
            "country": "ch"
        }

    def scrape(self):
        all_jobs = []
    
        try:
            response = requests.get(self.url, params=self.params).json()
            jobs_on_page = response.get("content", [])
            all_jobs.extend(jobs_on_page)
        except Exception as e:
            logging.error(f"Unable to scrape {self.company}: {e}")
            return []
    
        self.current_listings.extend([
            MetGroupJobListing(
                listing_id=job["id"],
                title=job["name"],
                profession=job.get("function", {}).get("label", "N/A"),
                location=job.get("location", {}).get("fullLocation", "N/A"),
                link=f"https://jobs.smartrecruiters.com/METGroup/{job['id']}"
            )
            for job in all_jobs
        ])
    
        return self.current_listings


    def _create_listing_from_dict(self, data: Dict[str, Any]) -> MetGroupJobListing:
        """
        Required by JobScraper abstract class
        """
        return MetGroupJobListing(
            listing_id=data["id"],
            title=data["title"],
            profession=data["profession"],
            location=data.get("location", "N/A"),
            link=data.get("link", "")
        )
