from lib.base_joblisting import JobListing
from lib.base_scraper import JobScraper
from typing import List, Dict, Any
import requests
import xml.etree.ElementTree as ET
import re
import logging


class AxpoJobListing(JobListing):
    def __init__(self, listing_id: str, title: str, posted_date: str, link: str):
        self.id = listing_id
        self.title = title
        self.posted_date = posted_date
        self.link = link
        self.company = "Axpo"

    def get_id(self) -> str:
        return self.id

    def generate_telegram_message(self) -> str:
        return f"*{self.title}*\nPosted: {self.posted_date}\n[Link]({self.link})"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "posted_date": self.posted_date,
            "link": self.link
        }


class AxpoJobScraper(JobScraper):
    def __init__(self):
        super().__init__(company_name="Axpo")
        self.rss_url = "https://careers.axpo.com/jobs.rss"
        self.country = "Switzerland"
        # You can add more departments here
        self.departments = ["IT / Technology", "Trading"]
        self.logo_path = "lib/axpo.png"

    def scrape(self) -> List[AxpoJobListing]:
        """Scrape job listings from Axpo using RSS feed."""
        listings = []

        try:
            # Build RSS URL with filters
            # Note: Axpo uses Teamtailor which has an RSS feed with filters
            params = f"?country={self.country}"

            # If specific departments are set, filter by them
            # Otherwise get all jobs in Switzerland
            if self.departments:
                for dept in self.departments:
                    dept_url = f"{self.rss_url}{params}&department={dept.replace(' ', '+')}"
                    listings.extend(self._fetch_from_rss(dept_url))
            else:
                # Get all jobs in Switzerland
                dept_url = f"{self.rss_url}{params}"
                listings.extend(self._fetch_from_rss(dept_url))

            # Remove duplicates based on job ID
            seen_ids = set()
            unique_listings = []
            for listing in listings:
                if listing.id not in seen_ids:
                    seen_ids.add(listing.id)
                    unique_listings.append(listing)

            self.current_listings = unique_listings

        except Exception as e:
            logging.error(f"Error scraping Axpo jobs: {e}")

        return self.current_listings

    def _fetch_from_rss(self, rss_url: str) -> List[AxpoJobListing]:
        """Fetch and parse jobs from RSS feed."""
        listings = []

        try:
            response = requests.get(rss_url)
            if response.status_code != 200:
                logging.error(f"Axpo RSS returned {response.status_code}")
                return listings

            root = ET.fromstring(response.content)
            jobs = root.findall('.//item')

            for job in jobs:
                title_elem = job.find('title')
                link_elem = job.find('link')
                pub_date_elem = job.find('pubDate')

                if title_elem is None or link_elem is None:
                    continue

                title = title_elem.text
                link = link_elem.text
                pub_date = pub_date_elem.text if pub_date_elem is not None else ''

                # Extract job ID from link
                # Link format: https://careers.axpo.com/jobs/6493102-it-service-manager-w-m-d
                job_id_match = re.search(r'/jobs/(\d+)-', link)
                job_id = job_id_match.group(1) if job_id_match else link

                listing = AxpoJobListing(
                    listing_id=job_id,
                    title=title,
                    posted_date=pub_date,
                    link=link
                )
                listings.append(listing)

        except Exception as e:
            logging.error(f"Error fetching from Axpo RSS {rss_url}: {e}")

        return listings

    def _create_listing_from_dict(self, data: Dict[str, Any]) -> AxpoJobListing:
        """Convert a dictionary back into an AxpoJobListing object."""
        return AxpoJobListing(
            listing_id=data["id"],
            title=data["title"],
            posted_date=data["posted_date"],
            link=data["link"]
        )
