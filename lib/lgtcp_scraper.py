from lib.base_joblisting import JobListing
from lib.base_scraper import JobScraper
from typing import List, Dict, Any
import requests
import logging
import re


class LGTCPJobListing(JobListing):
    def __init__(self, listing_id: str, title: str, locations: str, link: str):
        self.id = listing_id
        self.title = title
        self.locations = locations
        self.link = link
        self.location_from_link = self.extract_location_from_url(link)

    def extract_location_from_url(self, url: str) -> str:
        """Extract the location part from the URL."""
        match = re.search(r'/job/([^/]+)/', url)
        return match.group(1).replace('-', ' ') if match else None

    def get_id(self) -> str:
        return self.id

    def generate_telegram_message(self) -> str:
        return (
            f"*{self.title}*\n"
            f"{self.locations}\n"
            f"Location from Link: {self.location_from_link}\n"
            f"[Link]({self.link})"
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "locations": self.locations,
            "link": self.link,
            "location_from_link": self.location_from_link,
        }


class LGTCPJobScraper(JobScraper):
    def __init__(self):
        super().__init__(company_name="LGTCP")
        self.logo_path = "lib/LGTCP.jpg"
        self.url = 'https://lgtcp.wd3.myworkdayjobs.com/wday/cxs/lgtcp/lgtcpcurrentvacancies/jobs'
        self.json_data = {
            'appliedFacets': {
                # Pfäffikon, Switzerland
                'locations': ['8e79cea3a59c01011b74930a4f6f0000'],
            },
            'limit': 20,
            'offset': 0,
            'searchText': '',
        }

    def scrape(self) -> List[LGTCPJobListing]:
        all_jobs = []
        total_jobs = None
        offset = 0
        limit = self.json_data['limit']

        while total_jobs is None or offset < total_jobs:
            self.json_data['offset'] = offset

            try:
                response = requests.post(self.url, json=self.json_data)
                response.raise_for_status()
                data = response.json()
            except Exception as e:
                logging.error(f"LGTCP scrape failed at offset {offset}: {e}")
                break

            if total_jobs is None:
                total_jobs = data.get('total', 0)

            jobs = data.get('jobPostings', [])
            for job in jobs:
                job_id = job.get('bulletFields', [None])[0]
                # e.g., "Student-Support---Data-analytics---Client-Services-Liquid-Markets-40-_JR1751-1"
                job_slug = job.get('externalPath').split('/')[-1]
                job_url = f"https://lgtcp.wd3.myworkdayjobs.com/en-US/lgtcpcurrentvacancies/details/{job_slug}"
                all_jobs.append(
                    LGTCPJobListing(
                        listing_id=job_id,
                        title=job.get('title'),
                        locations=job.get('locationsText'),
                        link=job_url
                        )
                    )
            offset += limit

        self.current_listings.extend(all_jobs)
        return self.current_listings

    def _create_listing_from_dict(self, data: Dict[str, Any]) -> LGTCPJobListing:
        return LGTCPJobListing(
            data["id"], data["title"], data["locations"], data["link"]
        )
