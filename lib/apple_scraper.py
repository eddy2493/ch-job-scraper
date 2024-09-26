from lib.base_joblisting import JobListing
from lib.base_scraper import JobScraper
from typing import List, Dict, Any
import requests
import logging
import re
import json

class AppleJobListing(JobListing):
    def __init__(self, listing_id: str, title:str, team: str, description: str):
        self.id = listing_id
        self.title = title
        self.team = team
        self.description = description
        self.link = "https://jobs.apple.com/de-ch/details/"+str(listing_id)

    def get_id(self):
        return self.id

    def generate_telegram_message(self):
        return f"{self.title} {self.id}\n{self.team}\n[Link]({self.link})"

    def to_dict(self):
        return {"id": self.id, "title": self.title, "team": self.team, "description": self.description, "link": self.link}


class AppleJobScraper(JobScraper):
    def __init__(self):
        super().__init__(company_name="Apple")
        self.logo_path = "lib/apple.png"
        self.url = 'https://jobs.apple.com/de-ch/search'
        self.json_data = {
            'query': '',
            'filters': {
                'postingpostLocation': [
                    'postLocation-CHEC',
                ],
                'range': {
                    'standardWeeklyHours': {
                        'start': None,
                        'end': None,
                    },
                },
            },
            'page': 1,
            'locale': 'de-ch',
            'sort': '',
        }
    def scrape(self):
        all_jobs = []
        page = 1

        while True:
            self.json_data["page"] = page
            response = requests.post('https://jobs.apple.com/api/role/search', json=self.json_data).json()
            jobs_on_page = response['searchResults']
            all_jobs.extend(jobs_on_page)

            # Break when there are no more jobs to fetch
            if len(all_jobs) >= response['totalRecords']:
                break

            page += 1
        self.current_listings.extend([AppleJobListing(a["positionId"], a["postingTitle"], a["team"]["teamName"], a["jobSummary"]) for a in all_jobs])
        return self.current_listings
    def _create_listing_from_dict(self, data: Dict[str, Any]) -> AppleJobListing:
        return AppleJobListing(data["id"], data["title"], data["team"], data["description"])
