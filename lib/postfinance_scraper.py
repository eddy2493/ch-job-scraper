from lib.base_joblisting import JobListing
from lib.base_scraper import JobScraper
from typing import List, Dict, Any
from html import unescape
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
    # Keep only IT roles; the careers API groups them under this category (filter1).
    FILTER_KEYWORD = "Informatik"
    MAX_PAGES = 20

    def __init__(self):
        super().__init__(company_name="PostFinance")
        self.logo_path = "lib/postfinance.png"
        self.url = "https://jobs.postfinance.ch/services/recruiting/v1/jobs"
        self.locale = "de_DE"
        self.headers = {
            "accept": "*/*",
            "content-type": "application/json",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
            "origin": "https://jobs.postfinance.ch",
            "referer": "https://jobs.postfinance.ch/search?locale=de_DE&searchResultView=LIST",
        }

    def _payload(self, page: int) -> Dict[str, Any]:
        return {
            "locale": self.locale,
            "pageNumber": page,
            "sortBy": "",
            "keywords": "",
            "location": "",
            "facetFilters": {},
            "brand": "PostFinance",
            "skills": [],
            "categoryId": 0,
            "alertId": "",
            "rcmCandidateId": "",
        }

    def scrape(self) -> List[PostFinanceJobListing]:
        seen_ids = set()
        listings = []

        for page in range(self.MAX_PAGES):
            try:
                response = requests.post(self.url, headers=self.headers, json=self._payload(page))
                response.raise_for_status()
                data = response.json()
            except Exception as e:
                logging.error(f"PostFinance scrape failed: {e}")
                return []

            results = data.get("jobSearchResult", [])
            if not results:
                break

            new_on_page = 0
            for item in results:
                job = item.get("response", {})
                listing_id = str(job.get("id", ""))
                if not listing_id or listing_id in seen_ids:
                    continue
                seen_ids.add(listing_id)
                new_on_page += 1

                category = (job.get("filter1") or [""])[0]
                if self.FILTER_KEYWORD not in category:
                    continue

                title = job.get("unifiedStandardTitle", "")
                url_title = unescape(job.get("urlTitle", ""))
                link = f"https://jobs.postfinance.ch/PostFinance/job/{url_title}/{listing_id}-{self.locale}"

                # "Bern|Bern|BE|Schweiz|CHE " -> "Bern"
                cities = [loc.split("|")[0].strip() for loc in job.get("jobLocationShort", [])]
                city = ", ".join(dict.fromkeys(c for c in cities if c))

                wmin = (job.get("cust_WorkingTimeMin") or [""])[0]
                wmax = (job.get("cust_WorkingTimeMax") or [""])[0]
                pensum = f"{wmin}-{wmax}%" if wmin and wmax else (f"{wmin or wmax}%" if (wmin or wmax) else "")

                listings.append(PostFinanceJobListing(listing_id, title, link, category, city, pensum))

            total = data.get("totalJobs", 0)
            if new_on_page == 0 or len(seen_ids) >= total:
                break

        self.current_listings = listings
        return listings

    def _create_listing_from_dict(self, data: Dict[str, Any]) -> PostFinanceJobListing:
        return PostFinanceJobListing(
            data["id"], data["title"], data["link"],
            data["department"], data["city"], data["pensum"],
        )
