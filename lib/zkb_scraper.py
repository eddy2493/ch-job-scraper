from lib.base_joblisting import JobListing
from lib.base_scraper import JobScraper
from typing import List, Dict, Any
from bs4 import BeautifulSoup
import requests
import logging
import re


class ZKBJobListing(JobListing):
    def __init__(self, listing_id: str, title: str, link: str, locations: List[str], division: str, position: str, workload: str):
        self.id = listing_id
        self.title = title
        self.link = link
        self.company = "ZKB"
        self.locations = locations
        self.division = division
        self.position = position
        self.workload = workload

    def get_id(self) -> str:
        return self.id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "link": self.link,
            "company": self.company,
            "locations": self.locations,
            "division": self.division,
            "position": self.position,
            "workload": self.workload,
        }


class ZKBJobScraper(JobScraper):
    FILTER_AREAS = {
        "Asset Management / Portfolio Management",
        "IT / Business Engineering",
        "Investment Solutions",
        "Risk",
        "Trading / Sales / Kapitalmarkt",
        "Unternehmensentwicklung / Strategie / Nachhaltigkeit",
        "Sonstige Funktionen / Spezialaufgaben",
    }

    def __init__(self):
        super().__init__(company_name="ZKB")
        self.start_url = "https://apply.refline.ch/792841/search.html"
        self.logo_path = "lib/zkb.png"

    def scrape(self) -> List[ZKBJobListing]:
        response = requests.get(self.start_url)
        if response.status_code != 200:
            logging.error(f"Could not scrape ZKB (status={response.status_code})")
            return []

        soup = BeautifulSoup(response.content, "html.parser")
        table = soup.find("table", class_="searchResult")
        if not table:
            logging.warning("No job table found")
            return []

        listings = []
        tbody = table.find("tbody")
        for row in tbody.find_all("tr"):
            cells = row.find_all("td")
            division = cells[1].get_text(strip=True)
            if division not in self.FILTER_AREAS:
                continue  # skip rows outside the allowed areas
            job = self.extract_description(row)
            if job:
                listings.append(job)

        self.current_listings = listings
        return listings

    def extract_description(self, element: Any) -> ZKBJobListing:
        cells = element.find_all("td")

        # --- Title + Link ---
        header = cells[0].find("a")
        link = header["href"]
        title = header.get_text(strip=True)

        # --- Extract ID from URL (e.g., /792841/10516/pub/1) ---
        listing_id_match = re.search(r"/(\d+)/pub/", link)
        listing_id = listing_id_match.group(1) if listing_id_match else link

        # --- Division, Position, Workload, Locations ---
        division = cells[1].get_text(strip=True)
        locations = [cells[2].get_text(strip=True)]
        workload = cells[3].get_text(strip=True)
        position = title

        return ZKBJobListing(listing_id, title, link, locations, division, position, workload)

    def _create_listing_from_dict(self, data: Dict[str, Any]) -> ZKBJobListing:
        return ZKBJobListing(
            data["id"],
            data["title"],
            data["link"],
            data["locations"],
            data["division"],
            data["position"],
            data["workload"],
        )
