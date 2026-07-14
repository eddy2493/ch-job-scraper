from lib.base_joblisting import JobListing
from lib.base_scraper import JobScraper
from typing import List, Dict, Any
from urllib.parse import quote
import requests
import logging


class GlencoreJobListing(JobListing):
    def __init__(self, listing_id: str, title: str, location: str, department: str, link: str):
        self.id = listing_id
        self.title = title
        self.location = location
        self.department = department
        self.link = link
        self.company = "Glencore"

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


class GlencoreJobScraper(JobScraper):
    """Glencore's careers API is pre-filtered to the Baar (Zug) HQ, so every result is a
    Swiss role — no extra filtering needed."""

    BASE = "https://www.glencore.com/.rest/api/v2/careers/"
    SEARCH_CRITERIA = '{"country":[""],"city":["Baar"],"commodity":["!KCC"]}'

    def __init__(self):
        super().__init__(company_name="Glencore")
        self.logo_path = "lib/glencore.png"
        self.headers = {
            'accept': 'application/json, text/plain, */*',
            'referer': 'https://www.glencore.com/en/careers/jobs',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
        }

    def scrape(self) -> List[GlencoreJobListing]:
        listings = []
        try:
            url = (f"{self.BASE}?locale=en&sortBy=title-asc&offset=0&limit=100"
                   f"&searchCriteria={quote(self.SEARCH_CRITERIA)}&keyword=")
            resp = requests.get(url, headers=self.headers, timeout=20)
            if resp.status_code != 200:
                logging.error(f"Glencore API returned {resp.status_code}")
                return listings

            for job in resp.json().get("data", []):
                highlights = job.get("highlights", [])
                location = ", ".join(p for p in [job.get("city"), job.get("region"),
                                                 job.get("country")] if p)
                # highlights = [employment_type, location, function]; the function is the
                # 3rd entry and is absent on some postings.
                department = highlights[2] if len(highlights) >= 3 else ""

                listings.append(GlencoreJobListing(
                    listing_id=str(job.get("jobId", "")),
                    title=job.get("title", ""),
                    location=location,
                    department=department,
                    link=job.get("url", ""),
                ))

            self.current_listings = listings
            return listings

        except Exception as e:
            logging.error(f"Error scraping Glencore jobs: {e}")
            return []

    def _create_listing_from_dict(self, data: Dict[str, Any]) -> GlencoreJobListing:
        return GlencoreJobListing(
            listing_id=data["id"],
            title=data["title"],
            location=data["location"],
            department=data["department"],
            link=data["link"]
        )
