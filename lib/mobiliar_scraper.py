from lib.base_joblisting import JobListing
from lib.base_scraper import JobScraper
from typing import List, Dict, Any
import requests
import logging


class MobiliarJobListing(JobListing):
    def __init__(self, listing_id: str, title: str, link: str, department: str, location: str, pensum: str):
        self.id = listing_id
        self.title = title
        self.link = link
        self.department = department
        self.location = location
        self.pensum = pensum

    def get_id(self) -> str:
        return self.id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "link": self.link,
            "department": self.department,
            "location": self.location,
            "pensum": self.pensum,
        }


class MobiliarJobScraper(JobScraper):
    def __init__(self):
        super().__init__(company_name="Mobiliar")
        self.logo_path = "lib/mobiliar.png"
        self.url = "https://jobs.mobiliar.ch/services/recruiting/v1/jobs"
        self.headers = {
            "Accept": "*/*",
            "Content-Type": "application/json",
            "Origin": "https://jobs.mobiliar.ch",
            "Referer": "https://jobs.mobiliar.ch/search/",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        }
        self.payload = {
            "locale": "de_DE",
            "pageNumber": 0,
            "sortBy": "",
            "keywords": "",
            "location": "",
            "facetFilters": {
                "cust_postingDep": ["IT", "Finanzen", "Asset Management"],
            },
            "brand": "",
            "skills": [],
            "categoryId": 0,
            "alertId": "",
            "rcmCandidateId": "",
        }

    def scrape(self) -> List[MobiliarJobListing]:
        all_jobs = []
        page = 0

        while True:
            self.payload["pageNumber"] = page

            try:
                response = requests.post(self.url, headers=self.headers, json=self.payload)
                response.raise_for_status()
                data = response.json()
            except Exception as e:
                logging.error(f"Mobiliar scrape failed at page {page}: {e}")
                break

            jobs = data.get("jobSearchResult", [])
            total = data.get("totalJobs", 0)

            for job in jobs:
                r = job.get("response", {})
                job_id = str(r.get("id", ""))
                title = r.get("unifiedStandardTitle", "")
                url_title = r.get("urlTitle", "")
                link = f"https://jobs.mobiliar.ch/default/job/{url_title}/{job_id}-de_DE"
                department = ", ".join(r.get("cust_postingDep", []))
                location = ", ".join(r.get("jobLocationShort", []))
                pensum = r.get("cust_postingCatFTE", "")

                all_jobs.append(MobiliarJobListing(job_id, title, link, department, location, pensum))

            if len(all_jobs) >= total:
                break
            page += 1

        self.current_listings = all_jobs
        return all_jobs

    def _create_listing_from_dict(self, data: Dict[str, Any]) -> MobiliarJobListing:
        return MobiliarJobListing(
            data["id"], data["title"], data["link"],
            data["department"], data["location"], data["pensum"],
        )
