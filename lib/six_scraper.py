from lib.base_joblisting import JobListing
from lib.base_scraper import JobScraper
from typing import List, Dict, Any
import requests
import logging
from bs4 import BeautifulSoup


class SIXJobListing(JobListing):
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


class SIXJobScraper(JobScraper):
    def __init__(self):
        super().__init__(company_name="SIX")
        self.logo_path = "lib/six.png"
        self.url = "https://jobs.six-group.com/search/?createNewAlert=false&q=&optionsFacetsDD_customfield2=IT&optionsFacetsDD_country=CH&optionsFacetsDD_customfield1="
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
        }

    def scrape(self) -> List[SIXJobListing]:
        listings = []

        try:
            response = requests.get(self.url, headers=self.headers, timeout=15)
            if response.status_code != 200:
                logging.error(f"SIX returned {response.status_code}")
                return listings

            soup = BeautifulSoup(response.text, 'html.parser')
            seen = set()

            for a in soup.select('a[href*="/job/"]'):
                href = a.get('href', '')
                title = a.get_text(strip=True)
                if not title or href in seen:
                    continue
                seen.add(href)

                # Extract job ID from URL like /job/Zurich-Something/1234567890/
                parts = href.rstrip('/').split('/')
                job_id = parts[-1] if parts else ''

                # Extract location from URL (first part after /job/)
                location = ''
                if len(parts) >= 2:
                    location = parts[-2].split('-')[0]

                link = f"https://jobs.six-group.com{href}" if href.startswith('/') else href

                listings.append(SIXJobListing(
                    listing_id=job_id,
                    title=title,
                    location=location,
                    link=link
                ))

            self.current_listings = listings

        except Exception as e:
            logging.error(f"Error scraping SIX jobs: {e}")

        return listings

    def _create_listing_from_dict(self, data: Dict[str, Any]) -> SIXJobListing:
        return SIXJobListing(
            listing_id=data["id"],
            title=data["title"],
            location=data["location"],
            link=data["link"]
        )
