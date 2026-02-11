from lib.base_joblisting import JobListing
from lib.base_scraper import JobScraper
from typing import List, Dict, Any
import requests
import logging


class RedHatJobListing(JobListing):
    def __init__(self, listing_id: str, title: str, locations: str, link: str):
        self.id = listing_id
        self.title = title
        self.locations = locations
        self.link = link

    def get_id(self) -> str:
        return self.id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "locations": self.locations,
            "link": self.link,
        }


class RedHatJobScraper(JobScraper):
    def __init__(self):
        super().__init__(company_name="Red Hat")
        self.logo_path = "lib/redhat.png"
        self.url = "https://redhat.wd5.myworkdayjobs.com/wday/cxs/redhat/jobs/jobs"
        self.json_data = {
            "appliedFacets": {
                "a": ["187134fccb084a0ea9b4b95f23890dbe"],
            },
            "limit": 20,
            "offset": 0,
            "searchText": "",
        }

    def scrape(self) -> List[RedHatJobListing]:
        all_jobs = []
        total_jobs = None
        offset = 0
        limit = self.json_data["limit"]

        while total_jobs is None or offset < total_jobs:
            self.json_data["offset"] = offset

            try:
                response = requests.post(self.url, json=self.json_data)
                response.raise_for_status()
                data = response.json()
            except Exception as e:
                logging.error(f"Red Hat scrape failed at offset {offset}: {e}")
                break

            if total_jobs is None:
                total_jobs = data.get("total", 0)

            jobs = data.get("jobPostings", [])
            for job in jobs:
                if not job.get("title") or not job.get("externalPath"):
                    continue
                job_id = job.get("bulletFields", [None])[0]
                job_slug = job.get("externalPath").split("/")[-1]
                job_url = f"https://redhat.wd5.myworkdayjobs.com/en-US/jobs/details/{job_slug}"
                all_jobs.append(
                    RedHatJobListing(
                        listing_id=job_id,
                        title=job.get("title"),
                        locations=job.get("locationsText"),
                        link=job_url,
                    )
                )
            offset += limit

        self.current_listings = all_jobs
        return all_jobs

    def _create_listing_from_dict(self, data: Dict[str, Any]) -> RedHatJobListing:
        return RedHatJobListing(
            data["id"], data["title"], data["locations"], data["link"]
        )
