from lib.base_joblisting import JobListing
from lib.base_scraper import JobScraper
from typing import List, Dict, Any
import requests
import logging
from bs4 import BeautifulSoup

# -------------------------------
# Job Listing Class
# -------------------------------
class CitadelJobListing(JobListing):
    def __init__(self, listing_id: str, title: str, location: str, link: str):
        self.id = listing_id
        self.title = title
        self.location = location
        self.link = link

    def get_id(self):
        return self.id

    def generate_telegram_message(self):
        return f"{self.title}\nLocation: {self.location}\n[Link]({self.link})"

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "location": self.location,
            "link": self.link
        }

# -------------------------------
# Scraper Class
# -------------------------------
class CitadelJobScraper(JobScraper):
    def __init__(self):
        super().__init__(company_name="Citadel Securities")
        self.logo_path = "lib/citadel.png"
        self.url = "https://www.citadelsecurities.com/wp-admin/admin-ajax.php"
        self.headers = {
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'origin': 'https://www.citadelsecurities.com',
            'referer': 'https://www.citadelsecurities.com/careers/open-opportunities?location-filter=zurich',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64)',
            'x-requested-with': 'XMLHttpRequest',
        }
        self.data = 'location-filter=zurich&selected-job-sections=323,325,324,326&current_page=1&sort_order=DESC&per_page=10&action=careers_listing_filter'

    def scrape(self):
        all_jobs = []

        try:
            response = requests.post(self.url, headers=self.headers, data=self.data)
            json_data = response.json()
            html_content = json_data.get("content", "")
            
            soup = BeautifulSoup(html_content, "html.parser")
            job_cards = soup.select("a.careers-listing-card")

            for card in job_cards:
                link = card.get("href")
                title = card.get("data-position") or card.select_one("h2").get_text(strip=True)
                location = card.select_one(".careers-listing-card__location").get_text(strip=True)
                job_id = link.split("/")[-2]  # use last part of URL as ID

                all_jobs.append(CitadelJobListing(
                    listing_id=job_id,
                    title=title,
                    location=location,
                    link=link
                ))

        except Exception as e:
            logging.error(f"Unable to scrape {self.company}: {e}")

        self.current_listings.extend(all_jobs)
        return self.current_listings

    def _create_listing_from_dict(self, data: Dict[str, Any]) -> CitadelJobListing:
        return CitadelJobListing(
            listing_id=data["id"],
            title=data["title"],
            location=data.get("location", "N/A"),
            link=data.get("link", "")
        )

# -------------------------------
# Quick test
# -------------------------------
if __name__ == "__main__":
    scraper = CitadelJobScraper()
    jobs = scraper.scrape()
    print(f"Found {len(jobs)} jobs")
    for job in jobs:
        print(job.generate_telegram_message())
