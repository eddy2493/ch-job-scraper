from lib.base_joblisting import JobListing
from lib.base_scraper import JobScraper
from typing import List, Dict, Any
import requests
import xml.etree.ElementTree as ET
import re
import logging


class HuaweiJobListing(JobListing):
    def __init__(self, listing_id: str, title: str, posted_date: str, link: str):
        self.id = listing_id
        self.title = title
        self.posted_date = posted_date
        self.link = link
        self.company = "Huawei"

    def get_id(self) -> str:
        return self.id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "posted_date": self.posted_date,
            "link": self.link
        }


class HuaweiJobScraper(JobScraper):
    # careers.huaweirc.ch is the Zurich Research Center's own Teamtailor board,
    # so every posting is already CH-based and research/engineering focused --
    # no country or department filter needed (the feed's department tags are
    # empty anyway).
    def __init__(self):
        super().__init__(company_name="Huawei")
        self.rss_url = "https://careers.huaweirc.ch/jobs.rss"
        self.logo_path = "lib/huawei.png"

    def scrape(self) -> List[HuaweiJobListing]:
        """Scrape job listings from Huawei Zurich Research Center via RSS feed."""
        listings = []

        try:
            response = requests.get(self.rss_url)
            if response.status_code != 200:
                logging.error(f"Huawei RSS returned {response.status_code}")
                return []

            root = ET.fromstring(response.content)

            for job in root.findall('.//item'):
                title_elem = job.find('title')
                link_elem = job.find('link')
                pub_date_elem = job.find('pubDate')

                if title_elem is None or link_elem is None:
                    continue

                title = title_elem.text
                link = link_elem.text
                pub_date = pub_date_elem.text if pub_date_elem is not None else ''

                # Link format: https://careers.huaweirc.ch/jobs/7996042-competition-talent-program
                job_id_match = re.search(r'/jobs/(\d+)-', link)
                job_id = job_id_match.group(1) if job_id_match else link

                listings.append(HuaweiJobListing(
                    listing_id=job_id,
                    title=title,
                    posted_date=pub_date,
                    link=link
                ))

            self.current_listings = listings

        except Exception as e:
            logging.error(f"Error scraping Huawei jobs: {e}")

        return self.current_listings

    def _create_listing_from_dict(self, data: Dict[str, Any]) -> HuaweiJobListing:
        """Convert a dictionary back into a HuaweiJobListing object."""
        return HuaweiJobListing(
            listing_id=data["id"],
            title=data["title"],
            posted_date=data["posted_date"],
            link=data["link"]
        )
