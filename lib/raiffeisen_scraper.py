from lib.base_joblisting import JobListing
from lib.base_scraper import JobScraper
from typing import List, Dict, Any
import requests
import logging


class RaiffeisenJobListing(JobListing):
    def __init__(self, listing_id: str, title: str, location: str, department: str, link: str):
        self.id = listing_id
        self.title = title
        self.location = location
        self.department = department
        self.link = link
        self.company = "Raiffeisen"

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


class RaiffeisenJobScraper(JobScraper):
    """Raiffeisen runs on the prospective.ch ATS (medium id 1950). All jobs are in
    Switzerland, so we only narrow by job function (fachbereich) to IT / investment /
    analytics / risk roles, plus quant/trading/portfolio matches by title.
    """

    API_URL = "https://ohws.prospective.ch/public/v1/medium/1950/jobs"
    PAGE_SIZE = 100
    MAX_PAGES = 20

    KEEP_FACHBEREICH = {"informatik", "investment", "analytik", "risk management"}
    TITLE_KEYWORDS = ("quant", "trading", "handel", "händler", "portfolio")

    def __init__(self):
        super().__init__(company_name="Raiffeisen")
        self.logo_path = "lib/raiffeisen.png"
        self.headers = {
            'accept': '*/*',
            'origin': 'https://jobs.raiffeisen.ch',
            'referer': 'https://jobs.raiffeisen.ch/',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
        }

    def _keep(self, title: str, fachbereich: List[str]) -> bool:
        if any(f.lower() in self.KEEP_FACHBEREICH for f in fachbereich):
            return True
        return any(kw in title.lower() for kw in self.TITLE_KEYWORDS)

    def scrape(self) -> List[RaiffeisenJobListing]:
        listings = []

        try:
            for page in range(self.MAX_PAGES):
                offset = page * self.PAGE_SIZE
                params = {"lang": "de", "offset": offset, "limit": self.PAGE_SIZE}
                resp = requests.get(self.API_URL, headers=self.headers, params=params, timeout=20)
                if resp.status_code != 200:
                    logging.error(f"Raiffeisen API returned {resp.status_code}")
                    break

                data = resp.json()
                jobs = data.get("jobs", [])
                total = data.get("total", 0)
                if not jobs:
                    break

                for job in jobs:
                    attrs = job.get("attributes", {})
                    fachbereich = attrs.get("fachbereich", [])
                    title = job.get("title", "")
                    if not self._keep(title, fachbereich):
                        continue

                    location = ", ".join(attrs.get("arbeitsort", []))
                    department = ", ".join(fachbereich)
                    link = job.get("links", {}).get("directlink", "")

                    listings.append(RaiffeisenJobListing(
                        listing_id=str(job.get("id", "")),
                        title=title,
                        location=location,
                        department=department,
                        link=link,
                    ))

                if offset + len(jobs) >= total:
                    break

            self.current_listings = listings
            return listings

        except Exception as e:
            logging.error(f"Error scraping Raiffeisen jobs: {e}")
            return []

    def _create_listing_from_dict(self, data: Dict[str, Any]) -> RaiffeisenJobListing:
        return RaiffeisenJobListing(
            listing_id=data["id"],
            title=data["title"],
            location=data["location"],
            department=data["department"],
            link=data["link"]
        )
