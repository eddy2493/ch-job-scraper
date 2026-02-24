from lib.base_joblisting import JobListing
from lib.base_scraper import JobScraper
from typing import List, Dict, Any
import requests
import logging


class ThomsonReutersJobListing(JobListing):
    def __init__(self, listing_id: str, title: str, location: str, link: str):
        self.id = listing_id
        self.title = title
        self.location = location
        self.link = link

    def get_id(self) -> str:
        return self.id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "location": self.location,
            "link": self.link
        }


class ThomsonReutersJobScraper(JobScraper):
    BASE_URL = "https://thomsonreuters.wd5.myworkdayjobs.com"
    SITE_PATH = "/en-US/External_Career_Site"
    JOBS_API = "/wday/cxs/thomsonreuters/External_Career_Site/jobs"
    # Switzerland location hierarchy ID from Workday facets
    LOCATION_ID = "d96c3728c0cb0117ac2ed2dd0c0cce54"

    def __init__(self):
        super().__init__(company_name="Thomson Reuters")
        self.logo_path = "lib/thomsonreuters.png"

    def scrape(self) -> List[ThomsonReutersJobListing]:
        listings = []
        session = requests.Session()

        try:
            # Initialize session to obtain CSRF token cookie
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9',
            })
            init_url = f"{self.BASE_URL}{self.SITE_PATH}?locationHierarchy2={self.LOCATION_ID}"
            session.get(init_url, timeout=15)

            csrf_token = session.cookies.get("CALYPSO_CSRF_TOKEN")
            if not csrf_token:
                logging.error("Thomson Reuters: failed to obtain CSRF token")
                return listings

            offset = 0
            limit = 20
            total = None

            while total is None or offset < total:
                payload = {
                    "appliedFacets": {"locationHierarchy2": [self.LOCATION_ID]},
                    "limit": limit,
                    "offset": offset,
                    "searchText": ""
                }
                headers = {
                    'accept': 'application/json',
                    'content-type': 'application/json',
                    'x-calypso-csrf-token': csrf_token,
                    'referer': init_url,
                }
                resp = session.post(
                    f"{self.BASE_URL}{self.JOBS_API}",
                    json=payload,
                    headers=headers,
                    timeout=15
                )

                if resp.status_code != 200:
                    logging.error(f"Thomson Reuters jobs API returned {resp.status_code}")
                    break

                data = resp.json()

                if total is None:
                    total = data.get("total", 0)
                    if total == 0:
                        break

                job_postings = data.get("jobPostings", [])
                if not job_postings:
                    break

                for job in job_postings:
                    external_path = job.get("externalPath", "")
                    link = f"{self.BASE_URL}{self.SITE_PATH}{external_path}"
                    listings.append(ThomsonReutersJobListing(
                        listing_id=external_path,
                        title=job.get("title", ""),
                        location=job.get("locationsText", ""),
                        link=link
                    ))

                offset += limit

            self.current_listings = listings

        except Exception as e:
            logging.error(f"Error scraping Thomson Reuters jobs: {e}")

        return listings

    def _create_listing_from_dict(self, data: Dict[str, Any]) -> ThomsonReutersJobListing:
        return ThomsonReutersJobListing(
            listing_id=data["id"],
            title=data["title"],
            location=data["location"],
            link=data["link"]
        )
