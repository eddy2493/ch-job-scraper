from lib.base_joblisting import JobListing
from lib.base_scraper import JobScraper
from typing import List, Dict, Any
import requests
import logging
import re
import json
 
class MicrosoftJobListing(JobListing):
    def __init__(self, listing_id: str, title:str, profession: str):
        self.id = listing_id
        self.title = title
        self.profession = profession
        self.link = f"https://jobs.careers.microsoft.com/global/en/job/{listing_id}/"
        
    def get_id(self):
        return self.id

    def generate_telegram_message(self):
        return f"{self.title} {self.id}\n{self.profession}\n[Link]({self.link})"

    def to_dict(self):
        return {"id": self.id, "title": self.title, "profession": self.profession, "link": self.link}

class MicrosoftJobScraper(JobScraper):
    def __init__(self):
        super().__init__(company_name="Microsoft")
        self.logo_path = "lib/microsoft.png"
        self.url = 'https://gcsservices.careers.microsoft.com/search/api/v1/search'
        self.params = {
            'lc': 'Switzerland',
            'l': 'en_us',
            'pg': '1',
            'pgSz': '20',
            'o': 'Relevance',
            'flt': 'true',
        }
    def scrape(self):
        all_jobs = []
        page = 1

        while True:
            self.params["pg"] = str(page)
            try:
                response = requests.get(self.url, params=self.params).json()
                jobs_on_page = response["operationResult"]["result"]["jobs"]
                all_jobs.extend(jobs_on_page)
            except:
                logging.error(f"Unable to scrape {self.company}")

            # Break when there are no more jobs to fetch
            if len(all_jobs) >= response["operationResult"]["result"]["totalJobs"]:
                break
            page += 1
            
        self.current_listings.extend([MicrosoftJobListing(a["jobId"], a["title"], a["properties"]["profession"]) for a in all_jobs])
        return self.current_listings
    def _create_listing_from_dict(self, data: Dict[str, Any]) -> MicrosoftJobListing:
        return MicrosoftJobListing(data["id"], data["title"], data["profession"])