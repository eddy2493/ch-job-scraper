from lib.base_joblisting import JobListing
from lib.base_scraper import JobScraper
from typing import List, Dict, Any
import requests
import logging


class BundesverwaltungJobListing(JobListing):
    def __init__(self, listing_id: str, title: str, location: str, department: str, link: str):
        self.id = listing_id
        self.title = title
        self.location = location
        self.department = department
        self.link = link
        self.company = "Bundesverwaltung"

    def get_id(self) -> str:
        return self.id

    def generate_telegram_message(self) -> str:
        return f"*{self.title}*\n{self.department}\n{self.location}\n[Link]({self.link})"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "location": self.location,
            "department": self.department,
            "link": self.link
        }


class BundesverwaltungJobScraper(JobScraper):
    def __init__(self):
        super().__init__(company_name="Bundesverwaltung")
        self.api_url = "https://ohws.prospective.ch/public/v1/medium/1000624/jobs"
        self.taetigkeitsbereich = "Informatik"
        self.logo_path = "lib/bundesverwaltung.png"

    def scrape(self) -> List[BundesverwaltungJobListing]:
        """Scrape Informatik job listings from Bundesverwaltung."""
        listings = []

        headers = {
            'accept': '*/*',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
        }

        try:
            # The API supports pagination, fetch all jobs
            offset = 0
            limit = 100

            while True:
                params = {
                    'lang': 'de',
                    'offset': offset,
                    'limit': limit
                }

                response = requests.get(self.api_url, headers=headers, params=params)

                if response.status_code != 200:
                    logging.error(f"Bundesverwaltung API returned {response.status_code}")
                    break

                data = response.json()
                jobs = data.get('jobs', [])

                if not jobs:
                    break

                # Filter for Informatik jobs
                for job in jobs:
                    taetigkeitsbereiche = job.get('attributes', {}).get('taetigkeitsbereich', [])

                    if self.taetigkeitsbereich in taetigkeitsbereiche:
                        job_id = job.get('id', '')
                        title = job.get('title', '')

                        # Get location
                        locations = job.get('attributes', {}).get('arbeitsort', [])
                        location = ', '.join(locations) if locations else 'Switzerland'

                        # Get department
                        departments = job.get('attributes', {}).get('verwaltungseinheit', [])
                        department = departments[0] if departments else ''

                        # Build job URL
                        viewkey = job.get('viewkey', '')
                        link = f"https://jobs.admin.ch/job/{viewkey}"

                        listing = BundesverwaltungJobListing(
                            listing_id=job_id,
                            title=title,
                            location=location,
                            department=department,
                            link=link
                        )
                        listings.append(listing)

                # Check if we've fetched all jobs
                if len(jobs) < limit or offset + len(jobs) >= data.get('total', 0):
                    break

                offset += limit

            self.current_listings = listings

        except Exception as e:
            logging.error(f"Error scraping Bundesverwaltung jobs: {e}")

        return listings

    def _create_listing_from_dict(self, data: Dict[str, Any]) -> BundesverwaltungJobListing:
        """Convert a dictionary back into a BundesverwaltungJobListing object."""
        return BundesverwaltungJobListing(
            listing_id=data["id"],
            title=data["title"],
            location=data["location"],
            department=data["department"],
            link=data["link"]
        )
