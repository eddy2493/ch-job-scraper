from lib.base_joblisting import JobListing
from lib.base_scraper import JobScraper
from typing import List, Dict, Any
import requests
import logging

class NvidiaJobListing(JobListing):
    def __init__(self, listing_id: str, title: str, locations: str, link: str):
        self.id = listing_id
        self.title = title
        self.locations = locations
        self.link = link

    def get_id(self):
        return self.id

    def generate_telegram_message(self):
        return f"{self.title} {self.id}\n{self.locations}\n[Link]({self.link})"

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "locations": self.locations,
            "link": self.link
        }


class NvidiaJobScraper(JobScraper):
    def __init__(self):
        super().__init__(company_name="Nvidia")
        self.logo_path = "lib/nvidia.png"
        self.url = 'https://nvidia.wd5.myworkdayjobs.com/wday/cxs/nvidia/NVIDIAExternalCareerSite/jobs'
        self.json_data = {
            'appliedFacets': {
                'locationHierarchy1': [
                    '2fcb99c455831013ea52e9ef1a0032ba',  # Switzerland example
                ],
            },
            'limit': 20,  # jobs per page
            'offset': 0,  # start offset
            'searchText': '',
        }

    def scrape(self):
        all_jobs = []
        total_jobs = None
        offset = 0
        limit = self.json_data['limit']

        while total_jobs is None or offset < total_jobs:
            self.json_data['offset'] = offset
            response = requests.post(self.url, json=self.json_data)
            data = response.json()

            if total_jobs is None:
                total_jobs = data.get('total', 0)

            for job in data.get('jobPostings', []):
                job_id = job.get('bulletFields', [None])[0]
                external_path = job.get('externalPath', '')
                # Correct full URL
                job_url = f"https://nvidia.wd5.myworkdayjobs.com/en-US/NVIDIAExternalCareerSite{external_path}" if external_path else None

                job_info = NvidiaJobListing(
                    listing_id=job_id or 'N/A',
                    title=job.get('title', 'No Title'),
                    locations=job.get('locationsText', 'No Location'),
                    link=job_url or 'No Link'
                )
                all_jobs.append(job_info)

            offset += limit

        self.current_listings.extend(all_jobs)
        return self.current_listings

    def _create_listing_from_dict(self, data: Dict[str, Any]) -> NvidiaJobListing:
        return NvidiaJobListing(
            data["id"],
            data["title"],
            data["locations"],
            data["link"]
        )
