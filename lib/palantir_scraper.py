from lib.base_joblisting import JobListing
from lib.base_scraper import JobScraper
from typing import List, Dict, Any
import requests
import logging


class PalantirJobListing(JobListing):
    def __init__(self, listing_id: str, title: str, location: str, department: str, link: str):
        self.id = listing_id
        self.title = title
        self.location = location
        self.department = department
        self.link = link
        self.company = "Palantir"

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


class PalantirJobScraper(JobScraper):
    # Palantir has a Zurich office; keep postings whose location is in Switzerland.
    CH_CITIES = ("zurich", "zürich", "geneva", "genève", "genf", "zug", "basel",
                 "bern", "lausanne", "baar", "pfäffikon", "pfaffikon", "lugano",
                 "winterthur", "switzerland", "suisse")

    def __init__(self):
        super().__init__(company_name="Palantir")
        self.api_url = "https://api.lever.co/v0/postings/palantir?mode=json"
        self.logo_path = "lib/palantir.png"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
        }

    def _is_swiss(self, job: Dict[str, Any]) -> bool:
        categories = job.get("categories", {}) or {}
        locations = [categories.get("location", "")]
        locations += categories.get("allLocations") or []
        blob = " ".join(locations).lower()
        return any(city in blob for city in self.CH_CITIES)

    def scrape(self) -> List[PalantirJobListing]:
        listings = []

        try:
            response = requests.get(self.api_url, headers=self.headers, timeout=20)
            if response.status_code != 200:
                logging.error(f"Palantir Lever API returned {response.status_code}")
                return listings

            jobs = response.json()
            if not isinstance(jobs, list):
                logging.error("Palantir Lever API returned unexpected payload")
                return listings

            for job in jobs:
                if not self._is_swiss(job):
                    continue

                categories = job.get("categories", {}) or {}
                listings.append(PalantirJobListing(
                    listing_id=str(job.get('id', '')),
                    title=job.get('text', ''),
                    location=categories.get('location', ''),
                    department=categories.get('team', ''),
                    link=job.get('hostedUrl', '')
                ))

            self.current_listings = listings

        except Exception as e:
            logging.error(f"Error scraping Palantir jobs: {e}")

        return listings

    def _create_listing_from_dict(self, data: Dict[str, Any]) -> PalantirJobListing:
        return PalantirJobListing(
            listing_id=data["id"],
            title=data["title"],
            location=data["location"],
            department=data["department"],
            link=data["link"]
        )
