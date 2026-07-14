from lib.base_joblisting import JobListing
from lib.base_scraper import JobScraper
from typing import List, Dict, Any
from bs4 import BeautifulSoup
import requests
import logging
import re


class WorldQuantJobListing(JobListing):
    def __init__(self, listing_id: str, title: str, location: str, department: str, link: str):
        self.id = listing_id
        self.title = title
        self.location = location
        self.department = department
        self.link = link
        self.company = "WorldQuant"

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


class WorldQuantJobScraper(JobScraper):
    # WorldQuant has Swiss offices in Zug and Geneva; a posting's data-location is a
    # pipe-separated list of office slugs, so keep any posting that includes one.
    CH_LOCATION_SLUGS = ("zug-switzerland", "geneva-switzerland")
    BASE = "https://www.worldquant.com/career-listing/"

    def __init__(self):
        super().__init__(company_name="WorldQuant")
        self.url = self.BASE
        self.logo_path = "lib/worldquant.png"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
        }

    def scrape(self) -> List[WorldQuantJobListing]:
        listings = []

        try:
            response = requests.get(self.url, headers=self.headers, timeout=20)
            if response.status_code != 200:
                logging.error(f"WorldQuant returned {response.status_code}")
                return listings

            soup = BeautifulSoup(response.text, 'html.parser')

            for li in soup.select('.cg-list li'):
                data_location = (li.get('data-location') or '').lower()
                if not any(slug in data_location for slug in self.CH_LOCATION_SLUGS):
                    continue

                a = li.select_one('a.fo-link')
                if not a:
                    continue

                href = a.get('href', '')
                match = re.search(r'id=(\d+)', href)
                if not match:
                    continue
                job_id = match.group(1)
                link = f"{self.BASE}?id={job_id}"

                title_elem = li.select_one('h4')
                title = title_elem.get_text(strip=True) if title_elem else ''

                loc_elem = li.select_one('.fo-location')
                location = loc_elem.get_text(strip=True) if loc_elem else ''

                dept_slug = li.get('data-department', '')
                department = dept_slug.replace('-', ' ').title()

                listings.append(WorldQuantJobListing(
                    listing_id=job_id,
                    title=title,
                    location=location,
                    department=department,
                    link=link
                ))

            self.current_listings = listings

        except Exception as e:
            logging.error(f"Error scraping WorldQuant jobs: {e}")

        return listings

    def _create_listing_from_dict(self, data: Dict[str, Any]) -> WorldQuantJobListing:
        return WorldQuantJobListing(
            listing_id=data["id"],
            title=data["title"],
            location=data["location"],
            department=data["department"],
            link=data["link"]
        )
