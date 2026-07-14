from lib.base_joblisting import JobListing
from lib.base_scraper import JobScraper
from typing import List, Dict, Any
import requests
import logging


class SquarepointJobListing(JobListing):
    def __init__(self, listing_id: str, title: str, location: str, department: str, link: str):
        self.id = listing_id
        self.title = title
        self.location = location
        self.department = department
        self.link = link
        self.company = "Squarepoint"

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


class SquarepointJobScraper(JobScraper):
    # Squarepoint's Greenhouse board lists roles across many offices; keep only
    # postings that include a Swiss office.
    CH_OFFICES = {"geneva", "zug", "zurich", "zürich", "lausanne", "basel", "bern"}
    # Greenhouse office ids for Squarepoint's Swiss locations (Zug, Geneva), used to
    # build the site's job-detail links. The Greenhouse API's absolute_url points at a
    # broken SPA path, so we construct the working /opportunity-details link instead.
    CH_OFFICE_IDS = "14638,14637"  # Zug, Geneva

    def __init__(self):
        super().__init__(company_name="Squarepoint")
        # content=true is required for the departments/offices fields to be populated.
        self.api_url = "https://boards-api.greenhouse.io/v1/boards/squarepointcapital/jobs?content=true"
        self.logo_path = "lib/squarepoint.png"
        self.headers = {
            'accept': '*/*',
            'origin': 'https://www.squarepoint-capital.com',
            'referer': 'https://www.squarepoint-capital.com/',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
        }

    def _is_swiss(self, job: Dict[str, Any]) -> bool:
        offices = [o.get("name", "").lower() for o in job.get("offices", [])]
        if any(office in self.CH_OFFICES for office in offices):
            return True
        # Fall back to the location string ("Geneva, London, Zug, ...")
        location = job.get("location", {}).get("name", "").lower()
        return any(city in location for city in self.CH_OFFICES)

    def scrape(self) -> List[SquarepointJobListing]:
        listings = []

        try:
            response = requests.get(self.api_url, headers=self.headers)

            if response.status_code != 200:
                logging.error(f"Squarepoint Greenhouse API returned {response.status_code}")
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

                link = (f"https://www.squarepoint-capital.com/opportunity-details"
                        f"?id={job_id}&gh_jid={job_id}&loc={self.CH_OFFICE_IDS}")

                listings.append(SquarepointJobListing(
                    listing_id=job_id,
                    title=title,
                    location=location,
                    department=department,
                    link=link
                ))

            self.current_listings = listings

        except Exception as e:
            logging.error(f"Error scraping Squarepoint jobs: {e}")

        return listings

    def _create_listing_from_dict(self, data: Dict[str, Any]) -> SquarepointJobListing:
        return SquarepointJobListing(
            listing_id=data["id"],
            title=data["title"],
            location=data["location"],
            department=data["department"],
            link=data["link"]
        )
