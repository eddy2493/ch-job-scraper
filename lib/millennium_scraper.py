from lib.base_joblisting import JobListing
from lib.base_scraper import JobScraper
from typing import List, Dict, Any
import requests
import logging


class MillenniumJobListing(JobListing):
    def __init__(self, listing_id: str, title: str, location: str, department: str, link: str):
        self.id = listing_id
        self.title = title
        self.location = location
        self.department = department
        self.link = link

    def get_id(self) -> str:
        return self.id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "location": self.location,
            "department": self.department,
            "link": self.link
        }


class MillenniumJobScraper(JobScraper):
    def __init__(self):
        super().__init__(company_name="Millennium")
        self.logo_path = "lib/millennium.png"
        self.api_url = "https://career.mlp.com/api/apply/v2/jobs"
        self.headers = {
            'Referer': 'https://career.mlp.com/careers?domain=mlp.com&sort_by=relevance',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
            'content-type': 'application/json'
        }
        self.page_size = 10

    def scrape(self) -> List[MillenniumJobListing]:
        listings = []
        start = 0

        try:
            while True:
                params = {
                    'domain': 'mlp.com',
                    'start': start,
                    'num': self.page_size,
                    'location': 'Switzerland',
                    'sort_by': 'relevance'
                }

                response = requests.get(self.api_url, params=params, headers=self.headers, timeout=10)
                if response.status_code != 200:
                    logging.error(f"Millennium API returned {response.status_code}")
                    break

                data = response.json()
                jobs = data.get('positions', [])
                total = data.get('count', 0)

                for job in jobs:
                    jid = str(job.get('id', ''))
                    link = f"https://career.mlp.com/careers/job?domain=mlp.com&pid={jid}"
                    listings.append(MillenniumJobListing(
                        listing_id=jid,
                        title=job.get('name', ''),
                        location=job.get('location', ''),
                        department=job.get('department', ''),
                        link=link
                    ))

                start += self.page_size
                if start >= total:
                    break

            self.current_listings = listings

        except Exception as e:
            logging.error(f"Error scraping Millennium jobs: {e}")

        return listings

    def _create_listing_from_dict(self, data: Dict[str, Any]) -> MillenniumJobListing:
        return MillenniumJobListing(
            listing_id=data["id"],
            title=data["title"],
            location=data["location"],
            department=data["department"],
            link=data["link"]
        )
