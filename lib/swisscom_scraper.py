from lib.base_joblisting import JobListing
from lib.base_scraper import JobScraper
from typing import List, Dict, Any
import requests
import logging
import re


class SwisscomJobListing(JobListing):
    def __init__(self, listing_id: str, title: str, locations: str, link: str):
        self.id = listing_id
        self.title = title
        self.locations = locations
        self.link = link
        self.location_from_link = self.extract_location_from_url(link)

    def extract_location_from_url(self, url: str) -> str:
        match = re.search(r'/job/([^/]+)/', url)
        return match.group(1).replace('-', ' ') if match else None

    def get_id(self) -> str:
        return self.id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "locations": self.locations,
            "link": self.link,
            "location_from_link": self.location_from_link,
        }


class SwisscomJobScraper(JobScraper):
    def __init__(self):
        super().__init__(company_name="Swisscom")
        self.logo_path = "lib/swisscom.png"
        self.url = 'https://swisscom.wd103.myworkdayjobs.com/wday/cxs/swisscom/SwisscomExternalCareers/jobs'
        self.json_data = {
            'appliedFacets': {
                'jobFamilyGroup': [
                    '788b5ebbd1fe100714cd1c821dcc0000',
                    '788b5ebbd1fe100714cd53b87a350000',
                    '788b5ebbd1fe100714cd3651e1110000',
                    '788b5ebbd1fe100714cd74b9c6d40000',
                    '788b5ebbd1fe100714cd561ed9180000',
                ],
            },
            'limit': 20,
            'offset': 0,
            'searchText': '',
        }

    def scrape(self) -> List[SwisscomJobListing]:
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
                logging.error(f"Swisscom scrape failed at offset {offset}: {e}")
                break

            if total_jobs is None:
                total_jobs = data.get('total', 0)

            jobs = data.get('jobPostings', [])
            for job in jobs:
                if not job.get('title') or not job.get('externalPath'):
                    continue
                job_id = job.get('bulletFields', [None])[0]
                job_slug = job.get('externalPath').split('/')[-1]
                job_url = f"https://swisscom.wd103.myworkdayjobs.com/de-DE/SwisscomExternalCareers/details/{job_slug}"
                all_jobs.append(
                    SwisscomJobListing(
                        listing_id=job_id,
                        title=job.get('title'),
                        locations=job.get('locationsText'),
                        link=job_url
                    )
                )
            offset += limit

        self.current_listings.extend(all_jobs)
        return self.current_listings

    def _create_listing_from_dict(self, data: Dict[str, Any]) -> SwisscomJobListing:
        return SwisscomJobListing(
            data["id"], data["title"], data["locations"], data["link"]
        )
