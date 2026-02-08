from lib.base_joblisting import JobListing
from lib.base_scraper import JobScraper
from typing import List, Dict, Any
import requests
import logging

class MicrosoftJobListing(JobListing):
    def __init__(self, listing_id: str, title:str, department: str):
        self.id = listing_id
        self.title = title
        self.profession = department
        self.link = f"https://apply.careers.microsoft.com/careers/job/{listing_id}"

    def get_id(self):
        return self.id

    def to_dict(self):
        return {"id": self.id, "title": self.title, "profession": self.profession, "link": self.link}

class MicrosoftJobScraper(JobScraper):
    def __init__(self):
        super().__init__(company_name="Microsoft")
        self.logo_path = "lib/microsoft.png"
        self.url = 'https://apply.careers.microsoft.com/api/pcsx/search'
        self.params = {
            'domain': 'microsoft.com',
            'query': '',
            'location': 'switzerland',
            'start': '0',
            'sort_by': 'distance',
            'filter_include_remote': '1',
            'hl': 'en',
        }
        self.page_size = 10

    def scrape(self):
        all_jobs = []
        start = 0

        while True:
            self.params["start"] = str(start)
            try:
                response = requests.get(self.url, params=self.params)
                response.raise_for_status()
                positions = response.json()["data"]["positions"]
            except Exception as e:
                logging.error(f"Unable to scrape {self.company}: {e}")
                break

            if not positions:
                break

            all_jobs.extend(positions)
            if len(positions) < self.page_size:
                break
            start += self.page_size

        self.current_listings.extend([
            MicrosoftJobListing(str(a["id"]), a["name"], a.get("department", ""))
            for a in all_jobs
        ])
        return self.current_listings

    def _create_listing_from_dict(self, data: Dict[str, Any]) -> MicrosoftJobListing:
        return MicrosoftJobListing(data["id"], data["title"], data["profession"])
