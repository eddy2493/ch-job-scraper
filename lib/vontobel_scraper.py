from lib.base_joblisting import JobListing
from lib.base_scraper import JobScraper
from typing import List, Dict, Any
import requests
import logging
import re
import json


class VontobelJobListing(JobListing):
    def __init__(self, listing_id: str, title: str, location: str, department: str, link: str):
        self.id = listing_id
        self.title = title
        self.location = location
        self.department = department
        self.link = link

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


class VontobelJobScraper(JobScraper):
    def __init__(self):
        super().__init__(company_name="Vontobel")
        self.logo_path = "lib/vontobel.png"
        self.url = "https://www.vontobel.com/de-ch/ueber-vontobel/karriere/offene-stellen/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
        }
        self.location_filters = ["Zürich", "Basel"]

    def scrape(self) -> List[VontobelJobListing]:
        listings = []

        try:
            response = requests.get(self.url, headers=self.headers, timeout=15)
            if response.status_code != 200:
                logging.error(f"Vontobel returned {response.status_code}")
                return listings

            html = response.text
            jobs = self._extract_jobs(html)

            for job in jobs:
                location = job.get('locationDescription', '')
                if not any(loc in location for loc in self.location_filters):
                    continue

                job_url = "https://www.vontobel.com" + job.get('url', '')
                listings.append(VontobelJobListing(
                    listing_id=str(job.get('id', '')),
                    title=job.get('title', ''),
                    location=location,
                    department=job.get('jobOrgGf', ''),
                    link=job_url
                ))

            self.current_listings = listings

        except Exception as e:
            logging.error(f"Error scraping Vontobel jobs: {e}")

        return listings

    def _extract_jobs(self, html: str) -> list:
        """Extract jobs array from embedded Next.js RSC data."""
        idx = html.find('\\"jobs\\":[{')
        if idx == -1:
            return []

        start = idx + len('\\"jobs\\":')
        bracket = 0
        i = start
        while i < len(html):
            if html[i:i+2] == '\\"':
                i += 2
                continue
            if html[i] == '[':
                bracket += 1
            elif html[i] == ']':
                bracket -= 1
                if bracket == 0:
                    end = i + 1
                    break
            i += 1
        else:
            return []

        jobs_escaped = html[start:end]
        jobs_json = jobs_escaped.replace('\\"', '"').replace('\\\\', '\\')
        return json.loads(jobs_json)

    def _create_listing_from_dict(self, data: Dict[str, Any]) -> VontobelJobListing:
        return VontobelJobListing(
            listing_id=data["id"],
            title=data["title"],
            location=data["location"],
            department=data["department"],
            link=data["link"]
        )
