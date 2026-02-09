from lib.base_joblisting import JobListing
from lib.base_scraper import JobScraper
from typing import List, Dict, Any
import requests
import logging
import re
from html import unescape


class ZurichJobListing(JobListing):
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


class ZurichJobScraper(JobScraper):
    def __init__(self):
        super().__init__(company_name="Zurich Insurance")
        self.base_url = "https://www.careers.zurich.com/search/?createNewAlert=false&q=&locationsearch=&optionsFacetsDD_shifttype=&optionsFacetsDD_department=Information+Technology&optionsFacetsDD_customfield3=Switzerland"
        self.logo_path = "lib/zurich.png"

    def scrape(self) -> List[ZurichJobListing]:
        listings = []
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
            'Accept-Encoding': 'identity',
        })

        try:
            html = self._fetch_page(session, 1)
            if not html:
                return listings

            listings.extend(self._parse_jobs(html))

            total_pages = self._get_total_pages(html)
            for page in range(2, total_pages + 1):
                page_html = self._fetch_page(session, page)
                if page_html:
                    listings.extend(self._parse_jobs(page_html))

        except Exception as e:
            logging.error(f"Error scraping Zurich Insurance jobs: {e}")

        self.current_listings = listings
        return listings

    def _fetch_page(self, session: requests.Session, page: int) -> str:
        url = self.base_url if page == 1 else f"{self.base_url}&page={page}"
        response = session.get(url)
        if response.status_code != 200:
            logging.error(f"Zurich Insurance returned {response.status_code} for page {page}")
            return None
        return response.text

    def _parse_jobs(self, html: str) -> List[ZurichJobListing]:
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
            link = f"https://www.careers.zurich.com{path}"

            id_match = re.search(r'/(\d+)/', path)
            listing_id = id_match.group(1) if id_match else path

            loc_match = re.search(
                r'<span class="jobLocation">\s*\n\s*([^<]+)',
                row
            )
            location = loc_match.group(1).strip() if loc_match else "Zurich"

            jobs.append(ZurichJobListing(
                listing_id=listing_id,
                title=title,
                location=location,
                link=link
            ))

        return jobs

    def _get_total_pages(self, html: str) -> int:
        match = re.search(r'Page\s+\d+\s+of\s+(\d+)', html)
        return int(match.group(1)) if match else 1

    def _create_listing_from_dict(self, data: Dict[str, Any]) -> ZurichJobListing:
        return ZurichJobListing(
            listing_id=data["id"],
            title=data["title"],
            location=data["location"],
            link=data["link"]
        )
