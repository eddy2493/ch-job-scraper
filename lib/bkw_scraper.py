from lib.base_joblisting import JobListing
from lib.base_scraper import JobScraper
from typing import List, Dict, Any
import requests
import logging
import re
import json

class BKWJobListing(JobListing):
    def __init__(self, listing_id: str, title:str, description: str, url: str):
        self.id = listing_id
        self.title = title
        self.description = description
        self.link = url

    def get_id(self):
        return self.id

    def generate_telegram_message(self):
        return f"{self.title} {self.id}\n[Link]({self.link})"

    def to_dict(self):
        return {"id": self.id, "title": self.title,"description": self.description, "link": self.link}


class BKWJobScraper(JobScraper):
    def __init__(self):
        super().__init__(company_name="BKW")
        self.logo_path = "lib/bkw.png"
        self.url = 'https://jobs.bkw.com/_api/v1/structureddata'
        self.params = {
            'configFromContentElement': '82381',
            'language': 'de-ch',
        }
    def filter_jobs(self, jobs):
        filtered_jobs = []
        for job in jobs:
            for land in job["relations"]["Land"]:
                if land["id"] == '116':
                    for feld in job["relations"]["Berufsfeld"]:
                        if feld["id"] == '2503' or feld["id"]=='2497':
                            filtered_jobs.append(job)
                            break
                    break
            
        return filtered_jobs
    def scrape(self):
        all_jobs=[]
        response = requests.get(self.url, params=self.params).json()
        all_jobs = self.filter_jobs(response["data"])
        self.current_listings.extend([BKWJobListing(a["id"], a["title"], a["shadowSearchText"], a["url"]) for a in all_jobs])
        return self.current_listings
    def _create_listing_from_dict(self, data: Dict[str, Any]) -> BKWJobListing:
        return BKWJobListing(data["id"], data["title"], data["description"], data["link"])
