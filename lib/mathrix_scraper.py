from lib.base_joblisting import JobListing
from lib.base_scraper import JobScraper
from typing import List, Dict, Any
import requests
import logging


class MathrixJobListing(JobListing):
    def __init__(self, listing_id: str, title: str, location: str, posted_date: str, link: str):
        self.id = listing_id
        self.title = title
        self.location = location
        self.posted_date = posted_date
        self.link = link
        self.company = "Mathrix Group"

    def get_id(self) -> str:
        return self.id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "location": self.location,
            "posted_date": self.posted_date,
            "link": self.link
        }


class MathrixJobScraper(JobScraper):
    def __init__(self):
        super().__init__(company_name="Mathrix Group")
        self.api_url = "https://mathrix.recruitee.com/api/offers"
        self.country = "Switzerland"
        self.logo_path = "lib/mathrix.png"

    def scrape(self) -> List[MathrixJobListing]:
        """Scrape all job listings from Mathrix Group in Switzerland."""
        listings = []

        try:
            response = requests.get(self.api_url)

            if response.status_code != 200:
                logging.error(f"Mathrix API returned {response.status_code}")
                return listings

            data = response.json()
            offers = data.get('offers', [])

            for offer in offers:
                # Filter for Switzerland
                country = offer.get('country', '')
                location = offer.get('location', '')

                if self.country in country or 'Zurich' in location or 'Zug' in location:
                    job_id = str(offer.get('id', ''))
                    title = offer.get('title', '')
                    posted_date = offer.get('published_at', '')
                    careers_url = offer.get('careers_apply_url', '')

                    listing = MathrixJobListing(
                        listing_id=job_id,
                        title=title,
                        location=location,
                        posted_date=posted_date,
                        link=careers_url
                    )
                    listings.append(listing)

            self.current_listings = listings

        except Exception as e:
            logging.error(f"Error scraping Mathrix jobs: {e}")

        return listings

    def _create_listing_from_dict(self, data: Dict[str, Any]) -> MathrixJobListing:
        """Convert a dictionary back into a MathrixJobListing object."""
        return MathrixJobListing(
            listing_id=data["id"],
            title=data["title"],
            location=data["location"],
            posted_date=data["posted_date"],
            link=data["link"]
        )
