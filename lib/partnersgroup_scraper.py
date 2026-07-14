from lib.base_joblisting import JobListing
from lib.base_scraper import JobScraper
from typing import List, Dict, Any
import requests
import logging


class PartnersGroupJobListing(JobListing):
    def __init__(self, listing_id: str, title: str, location: str, department: str, link: str):
        self.id = listing_id
        self.title = title
        self.location = location
        self.department = department
        self.link = link
        self.company = "Partners Group"

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


class PartnersGroupJobScraper(JobScraper):
    """Partners Group (Baar/Zug) runs its careers on the connectid.cloud ATS. The public
    jobs endpoint is a POST with a bearer token embedded in the site's jobs-ats.js. Jobs
    are global, so we filter to Switzerland and to the on-profile functional areas
    (technology / investments / capital markets / quant & risk), plus quant/trading titles.
    """

    API_URL = "https://idxatsportal-prod-api.connectid.cloud/api/clients/67/jobs"
    # Public API token embedded in https://www.partnersgroup.com/en/javascripts/shared/jobs-ats.js
    API_TOKEN = ("56f067aa86809e1165da1621d1edbb9b6bcda4fc36b297be4fc1e5e1da4c2d230"
                 "a5c81d040cdfa994ecf9c2d1c05b9cb00d36527d73ed6611b695af86c049f80")
    JOB_URL = "https://www.partnersgroup.com/en/careers/open-positions/job-details/{reqid}"

    CH_TERMS = ("zug", "baar", "zurich", "zürich", "geneva", "switzerland", "schweiz", "luzern")
    KEEP_FUNCTIONS = {"technology", "investments", "investment services",
                      "capital markets", "quantitative & risk management"}
    TITLE_KEYWORDS = ("quant", "trading", "handel", "portfolio")

    def __init__(self):
        super().__init__(company_name="Partners Group")
        self.logo_path = "lib/partnersgroup.png"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
            "Authorization": f"Bearer {self.API_TOKEN}",
            "Content-Type": "application/json",
            "Origin": "https://www.partnersgroup.com",
            "Referer": "https://www.partnersgroup.com/",
        }

    def _is_swiss(self, job: Dict[str, Any]) -> bool:
        blob = " ".join([job.get("country", "") or "", job.get("city", "") or "",
                         job.get("location", "") or ""]).lower()
        return any(term in blob for term in self.CH_TERMS)

    def _keep(self, job: Dict[str, Any]) -> bool:
        function = (job.get("functionalareas", "") or "").lower()
        title = (job.get("externaltitle") or job.get("jobtitle") or "").lower()
        return function in self.KEEP_FUNCTIONS or any(kw in title for kw in self.TITLE_KEYWORDS)

    def scrape(self) -> List[PartnersGroupJobListing]:
        listings = []

        try:
            resp = requests.post(self.API_URL, headers=self.headers,
                                 json={"page": 1, "pageSize": 500}, timeout=20)
            if resp.status_code != 200:
                logging.error(f"Partners Group API returned {resp.status_code}")
                return listings

            for job in resp.json().get("jobs", []):
                if not self._is_swiss(job) or not self._keep(job):
                    continue

                reqid = str(job.get("jobreqid", ""))
                title = job.get("externaltitle") or job.get("jobtitle") or ""
                location = job.get("city") or job.get("location") or ""

                listings.append(PartnersGroupJobListing(
                    listing_id=reqid,
                    title=title,
                    location=location,
                    department=job.get("functionalareas", ""),
                    link=self.JOB_URL.format(reqid=reqid),
                ))

            self.current_listings = listings
            return listings

        except Exception as e:
            logging.error(f"Error scraping Partners Group jobs: {e}")
            return []

    def _create_listing_from_dict(self, data: Dict[str, Any]) -> PartnersGroupJobListing:
        return PartnersGroupJobListing(
            listing_id=data["id"],
            title=data["title"],
            location=data["location"],
            department=data["department"],
            link=data["link"]
        )
