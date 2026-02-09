from lib.base_joblisting import JobListing
from lib.base_scraper import JobScraper
from typing import List, Dict, Any
import requests
import logging
import re
from html import unescape


class SwissReJobListing(JobListing):
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


class SwissReJobScraper(JobScraper):
    def __init__(self):
        super().__init__(company_name="Swiss Re")
        self.base_url = "https://careers.swissre.com/search/"
        self.job_families = ["Asset+Management", "Data", "Finance", "Technology"]
        self.location = "Zurich, Zurich, CH"
        self.shifttype = "Regular Employment"
        self.logo_path = "lib/swissre.png"

    def _build_filter_url(self, job_family: str) -> str:
        return (
            f"{self.base_url}?q="
            f"&optionsFacetsDD_customfield2={job_family}"
            f"&optionsFacetsDD_location={self.location}"
            f"&optionsFacetsDD_shifttype={self.shifttype}"
        )

    def scrape(self) -> List[SwissReJobListing]:
        seen_ids = set()
        listings = []
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
            'Accept-Encoding': 'identity',
        })

        try:
            for family in self.job_families:
                filter_url = self._build_filter_url(family)
                html = self._fetch_page(session, filter_url, 1)
                if not html:
                    continue

                self._collect_jobs(html, listings, seen_ids)

                total_pages = self._get_total_pages(html)
                for page in range(2, total_pages + 1):
                    page_html = self._fetch_page(session, filter_url, page)
                    if page_html:
                        self._collect_jobs(page_html, listings, seen_ids)

        except Exception as e:
            logging.error(f"Error scraping Swiss Re jobs: {e}")

        self.current_listings = listings
        return listings

    def _fetch_page(self, session: requests.Session, filter_url: str, page: int) -> str:
        url = filter_url if page == 1 else f"{filter_url}&page={page}"
        response = session.get(url)
        if response.status_code != 200:
            logging.error(f"Swiss Re returned {response.status_code} for page {page}")
            return None
        return response.text

    def _collect_jobs(self, html: str, listings: List, seen_ids: set):
        for job in self._parse_jobs(html):
            if job.id not in seen_ids:
                seen_ids.add(job.id)
                listings.append(job)

    def _parse_jobs(self, html: str) -> List[SwissReJobListing]:
        jobs = []
        rows = re.findall(r'<tr class="data-row">(.*?)</tr>', html, re.DOTALL)

        for row in rows:
            title_match = re.search(
                r'<a\s+href="(/job/[^"]+)"\s+class="jobTitle-link">([^<]+)</a>',
                row
            )
            if not title_match:
                continue

            path = unescape(title_match.group(1))
            title = unescape(title_match.group(2).strip())
            link = f"https://careers.swissre.com{path}"

            id_match = re.search(r'/(\d+)/', path)
            listing_id = id_match.group(1) if id_match else path

            loc_match = re.search(
                r'<span class="jobLocation">\s*\n\s*([^<]+)',
                row
            )
            location = loc_match.group(1).strip() if loc_match else "Zurich"

            jobs.append(SwissReJobListing(
                listing_id=listing_id,
                title=title,
                location=location,
                link=link
            ))

        return jobs

    def _get_total_pages(self, html: str) -> int:
        match = re.search(r'Page\s+\d+\s+of\s+(\d+)', html)
        return int(match.group(1)) if match else 1

    def _create_listing_from_dict(self, data: Dict[str, Any]) -> SwissReJobListing:
        return SwissReJobListing(
            listing_id=data["id"],
            title=data["title"],
            location=data["location"],
            link=data["link"]
        )
