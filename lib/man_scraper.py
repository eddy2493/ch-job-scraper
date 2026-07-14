from lib.base_joblisting import JobListing
from lib.base_scraper import JobScraper
from typing import List, Dict, Any
import requests
import logging


class ManJobListing(JobListing):
    def __init__(self, listing_id: str, title: str, location: str, department: str, link: str):
        self.id = listing_id
        self.title = title
        self.location = location
        self.department = department
        self.link = link
        self.company = "Man Group"

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


class ManJobScraper(JobScraper):
    # Man Group's Swiss office is Pfäffikon (SZ); keep only postings there.
    CH_OFFICES = {"pfaffikon", "pfäffikon", "zurich", "zürich", "geneva", "zug", "switzerland"}

    def __init__(self):
        super().__init__(company_name="Man Group")
        # content=true is required for the departments/offices fields to be populated.
        self.api_url = "https://boards-api.greenhouse.io/v1/boards/mangroup/jobs?content=true"
        self.logo_path = "lib/man.png"
        self.headers = {
            'accept': '*/*',
            'referer': 'https://job-boards.eu.greenhouse.io/',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
        }

    def _is_swiss(self, job: Dict[str, Any]) -> bool:
        offices = [o.get("name", "").lower() for o in job.get("offices", [])]
        if any(office in self.CH_OFFICES for office in offices):
            return True
        location = job.get("location", {}).get("name", "").lower()
        return any(city in location for city in self.CH_OFFICES)

    def scrape(self) -> List[ManJobListing]:
        listings = []

        try:
            response = requests.get(self.api_url, headers=self.headers)

            if response.status_code != 200:
                logging.error(f"Man Group Greenhouse API returned {response.status_code}")
                return listings

            jobs = response.json().get('jobs', [])

            for job in jobs:
                if not self._is_swiss(job):
                    continue

                job_id = str(job.get('id', ''))
                title = job.get('title', '')
                location = job.get('location', {}).get('name', '')

                departments = job.get('departments', [])
                department = departments[0]['name'] if departments else ''

                listings.append(ManJobListing(
                    listing_id=job_id,
                    title=title,
                    location=location,
                    department=department,
                    link=job.get('absolute_url', '')
                ))

            self.current_listings = listings

        except Exception as e:
            logging.error(f"Error scraping Man Group jobs: {e}")

        return listings

    def _create_listing_from_dict(self, data: Dict[str, Any]) -> ManJobListing:
        return ManJobListing(
            listing_id=data["id"],
            title=data["title"],
            location=data["location"],
            department=data["department"],
            link=data["link"]
        )
