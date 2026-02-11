from lib.base_joblisting import JobListing
from lib.base_scraper import JobScraper
from typing import List, Dict, Any
import requests
import logging
from bs4 import BeautifulSoup


class SNBJobListing(JobListing):
    def __init__(self, listing_id: str, title: str, link: str):
        self.id = listing_id
        self.title = title
        self.link = link

    def get_id(self) -> str:
        return self.id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "link": self.link
        }


class SNBJobScraper(JobScraper):
    def __init__(self):
        super().__init__(company_name="SNB")
        self.logo_path = "lib/snb.png"
        self.url = "https://careers.snb.ch/search/?createNewAlert=false&q=&optionsFacetsDD_department=&optionsFacetsDD_customfield2="
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
        }
        self.it_keywords = [
            'it-', 'it ', 'ict', 'software', 'engineer', 'developer',
            'devops', 'applikationsentwickl', 'informatik',
            'data center', 'data science', 'cloud',
        ]

    def _is_it_related(self, title: str) -> bool:
        title_lower = title.lower()
        return any(kw in title_lower for kw in self.it_keywords)

    def scrape(self) -> List[SNBJobListing]:
        listings = []

        try:
            response = requests.get(self.url, headers=self.headers, timeout=15)
            if response.status_code != 200:
                logging.error(f"SNB returned {response.status_code}")
                return listings

            soup = BeautifulSoup(response.text, 'html.parser')
            seen = set()

            for a in soup.select('a.jobTitle-link'):
                job_id = a.get('data-focus-tile', '').replace('.job-id-', '')
                if not job_id or job_id in seen:
                    continue
                seen.add(job_id)

                title = a.get_text(strip=True)
                if not self._is_it_related(title):
                    continue

                href = a.get('href', '')
                link = f"https://careers.snb.ch{href}" if href.startswith('/') else href

                listings.append(SNBJobListing(
                    listing_id=job_id,
                    title=title,
                    link=link
                ))

            self.current_listings = listings

        except Exception as e:
            logging.error(f"Error scraping SNB jobs: {e}")

        return listings

    def _create_listing_from_dict(self, data: Dict[str, Any]) -> SNBJobListing:
        return SNBJobListing(
            listing_id=data["id"],
            title=data["title"],
            link=data["link"]
        )
