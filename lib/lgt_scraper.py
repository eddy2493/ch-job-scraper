from lib.base_joblisting import JobListing
from lib.base_scraper import JobScraper
from typing import List, Dict, Any
from bs4 import BeautifulSoup
import requests
import logging
import re


class LGTJobListing(JobListing):
    def __init__(self, listing_id: str, title: str, link: str, locations: List[str], division: str, position: str, workload: str):
        self.id = listing_id
        self.title = title
        self.link = link
        self.company = "LGT"
        self.locations = locations
        self.division = division
        self.position = position
        self.workload = workload

    def get_id(self) -> str:
        return self.id

    def generate_telegram_message(self) -> str:
        locations_str = ", ".join(self.locations)
        return f"*{self.title}* at {self.division}\n{locations_str}\n{self.position} ({self.workload})\n[Link]({self.link})"

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


class LGTJobScraper(JobScraper):
    def __init__(self):
        super().__init__(company_name="LGT")
        self.base_url = "https://www.lgt.com"
        self.start_url = "https://www.lgt.com/global-en/career/jobs/34662!jobSearch?q=&location=12412,287504&interests=12380,70290"
        self.logo_path = "lib/lgt.png"

    def scrape(self) -> List[LGTJobListing]:
        page_url = self.start_url
        while True:
            logging.info(f"Scraping page: {page_url}")
            response = requests.get(page_url)
            if response.status_code != 200:
                logging.error(f"Could not scrape LGT (status={response.status_code}, url={page_url})")
                break

            soup = BeautifulSoup(response.content, "html.parser")

            # --- Get all job blocks ---
            job_divs = soup.find_all("div", class_="lgt-teaser-list__element")
            for div in job_divs:
                job = self.extract_description(div)
                if job:
                    self.current_listings.append(job)

            # --- Handle pagination ---
            pagination_nav = soup.find("nav", class_="lgt-pagination")
            if pagination_nav:
                next_btn = pagination_nav.find("li", class_="lgt-pagination__next")
                if next_btn and next_btn.find("a"):
                    next_href = next_btn.find("a")["href"]
                    page_url = self.base_url + next_href
                else:
                    break  # no more next link
            else:
                break  # no pagination

        return self.current_listings

    def extract_description(self, element: Any) -> LGTJobListing:
        # --- Title + Link ---
        header = element.find("a", class_="lgt-link lgt-teaser__title-link")
        if not header:
            return None
        link = self.base_url + header["href"]
        title = header.get_text(strip=True)

        # --- Extract ID from URL (last --digits) ---
        listing_id_match = re.search(r"--(\d+)$", link)
        listing_id = listing_id_match.group(1) if listing_id_match else link

        # --- Locations ---
        locations = [li.get_text(strip=True) for li in element.select("ul.lgt-teaser__location li")]

        # --- Interests (Division, Position, Workload) ---
        interest_items = [li.get_text(strip=True) for li in element.select("ul.lgt-teaser__interest li")]
        division = interest_items[0] if len(interest_items) > 0 else ""
        position = interest_items[1] if len(interest_items) > 1 else ""
        workload = interest_items[2] if len(interest_items) > 2 else ""

        return LGTJobListing(listing_id, title, link, locations, division, position, workload)

    def _create_listing_from_dict(self, data: Dict[str, Any]) -> LGTJobListing:
        return LGTJobListing(
            data["id"],
            data["title"],
            data["link"],
            data["locations"],
            data["division"],
            data["position"],
            data["workload"],
        )
