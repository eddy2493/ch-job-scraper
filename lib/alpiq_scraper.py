from lib.base_joblisting import JobListing
from lib.base_scraper import JobScraper
from typing import List, Dict, Any
from bs4 import BeautifulSoup
import requests
import logging

class AlpiqJobListing(JobListing):
    def __init__(self, listing_id: str, title: str, link: str, locations: List[str], division: str, position: str, workload: str):
        self.id = listing_id
        self.title = title
        self.link = link
        self.company = "Alpiq"
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


class AlpiqJobScraper(JobScraper):
    def __init__(self):
        super().__init__(company_name="Alpiq")
        self.base_url = "https://www.alpiq.com/career/open-jobs/jobs/job-page-{page}/f1-1ee0b/f2-%2A/search"
        self.logo_path = "lib/alpiq.png"
        self.data = {
            'tx_successfactors_jobcollection[__referrer][@extension]': 'SuccessFactors',
            'tx_successfactors_jobcollection[__referrer][@controller]': 'Job',
            'tx_successfactors_jobcollection[__referrer][@action]': 'list',
            'tx_successfactors_jobcollection[__referrer][arguments]': 'YTowOnt973e50d85c7536a11bc1b8cc02f015de87fe6beb9',
            'tx_successfactors_jobcollection[__referrer][@request]': '{"@extension":"SuccessFactors","@controller":"Job","@action":"list"}23a1c8e999f0d3f5dacdb35e88ff0add77c03798',
            'tx_successfactors_jobcollection[__trustedProperties]': '{"filter":{"search":1,"filter1":[1,1,1,1,1],"filter2":[1,1,1,1,1,1,1,1,1]}}9c3d03d72f02c50ed62a451e138c4b1c486e6f0a',
            'tx_successfactors_jobcollection[filter][search]': '',
            'tx_successfactors_jobcollection[filter][filter1]': '',
            'tx_successfactors_jobcollection[filter][filter1][]': '1ee0b',
            'tx_successfactors_jobcollection[filter][filter2]': '',
        }

    def scrape(self) -> List[AlpiqJobListing]:
        listings = []
        page = 1

        while True:
            url = self.base_url.format(page=page)
            response = requests.post(url, data=self.data)
            if response.status_code != 200:
                logging.error(f"Failed to fetch page {page} (status={response.status_code})")
                break

            soup = BeautifulSoup(response.content, "html.parser")
            jobs = soup.find_all("ul", class_="job-item")
            if not jobs:
                break  # no more jobs

            for job_elem in jobs:
                job = self.extract_job(job_elem)
                if job:
                    listings.append(job)

            # Check if there is a next page
            pagination = soup.find("ul", class_="pagination")
            next_li = pagination.find("li", class_="next") if pagination else None
            if not next_li or not next_li.find("a"):
                break  # no next page

            page += 1

        self.current_listings = listings
        return listings

    def extract_job(self, element: Any) -> AlpiqJobListing:
        job_id = element.get("data-job-id")
        title_elem = element.find("a", class_="title")
        title = title_elem.get_text(strip=True)
        link = "https://www.alpiq.com" + title_elem["href"]

        division_elem = element.find("div", class_="tag")
        division = division_elem.get_text(strip=True) if division_elem else "Unknown"

        contract_elem = element.find("div", class_="contract")
        location, workload = ("Unknown", "Unknown")
        if contract_elem:
            spans = contract_elem.find_all("span")
            if len(spans) >= 1:
                loc_work = spans[0].get_text(strip=True).split(" - ")
                location = loc_work[0].strip()
                if len(loc_work) > 1:
                    workload = loc_work[1].strip()

        return AlpiqJobListing(
            listing_id=job_id,
            title=title,
            link=link,
            locations=[location],
            division=division,
            position=title,
            workload=workload
        )

    def _create_listing_from_dict(self, data: Dict[str, Any]) -> AlpiqJobListing:
        return AlpiqJobListing(
            data["id"],
            data["title"],
            data["link"],
            data["locations"],
            data["division"],
            data["position"],
            data["workload"],
        )
