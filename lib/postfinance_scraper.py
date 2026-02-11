from lib.base_joblisting import JobListing
from lib.base_scraper import JobScraper
from typing import List, Dict, Any
import requests
import logging


class PostFinanceJobListing(JobListing):
    def __init__(self, listing_id: str, title: str, link: str, department: str, city: str, pensum: str):
        self.id = listing_id
        self.title = title
        self.link = link
        self.department = department
        self.city = city
        self.pensum = pensum

    def get_id(self) -> str:
        return self.id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "link": self.link,
            "department": self.department,
            "city": self.city,
            "pensum": self.pensum,
        }


class PostFinanceJobScraper(JobScraper):
    FILTER_DEPARTMENTS = {
        "Informatik",
    }

    def __init__(self):
        super().__init__(company_name="PostFinance")
        self.logo_path = "lib/postfinance.png"
        self.url = "https://www.postfinance.ch/pfch/rest/api/job-tool/jobs/all"
        self.headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
            "referer": "https://www.postfinance.ch/de/ueber-uns/arbeiten-postfinance/offene-stellen.html",
        }

    def scrape(self) -> List[PostFinanceJobListing]:
        try:
            response = requests.get(self.url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            logging.error(f"PostFinance scrape failed: {e}")
            return []

        jobs = data.get("result", data) if isinstance(data, dict) else data

        listings = []
        for job in jobs:
            dept = job.get("department", {}).get("langDe", "")
            if dept not in self.FILTER_DEPARTMENTS:
                continue

            listing_id = str(job.get("id", ""))
            title = job.get("title", "")
            link = job.get("link", "")
            city = job.get("city", "")
            pensum = job.get("pensum", "")

            listings.append(PostFinanceJobListing(listing_id, title, link, dept, city, pensum))

        self.current_listings = listings
        return listings

    def _create_listing_from_dict(self, data: Dict[str, Any]) -> PostFinanceJobListing:
        return PostFinanceJobListing(
            data["id"], data["title"], data["link"],
            data["department"], data["city"], data["pensum"],
        )
