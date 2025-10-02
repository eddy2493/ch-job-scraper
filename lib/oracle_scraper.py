from lib.base_joblisting import JobListing
from lib.base_scraper import JobScraper
from typing import List, Dict, Any
import requests
import logging


class OracleJobListing(JobListing):
    def __init__(self, listing_id: str, title: str, location: str, posted_date: str, link: str):
        self.id = listing_id
        self.title = title
        self.location = location
        self.posted_date = posted_date
        self.link = link
        self.company = "Oracle"

    def get_id(self) -> str:
        return self.id

    def generate_telegram_message(self) -> str:
        return f"*{self.title}*\n{self.location}\nPosted: {self.posted_date}\n[Link]({self.link})"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "location": self.location,
            "posted_date": self.posted_date,
            "link": self.link
        }


class OracleJobScraper(JobScraper):
    def __init__(self):
        super().__init__(company_name="Oracle")
        self.api_url = "https://eeho.fa.us2.oraclecloud.com/hcmRestApi/resources/latest/recruitingCEJobRequisitions"
        self.location_facet = "300000000106764"  # Switzerland region
        self.country_code = "CH"  # Switzerland country code
        self.logo_path = "lib/oracle.png"

    def scrape(self) -> List[OracleJobListing]:
        """Scrape IT-related job listings from Oracle Switzerland."""
        listings = []

        headers = {
            'Accept': '*/*',
            'Content-Type': 'application/vnd.oracle.adf.resourceitem+json;charset=utf-8',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
        }

        params = {
            'onlyData': 'true',
            'expand': 'requisitionList.workLocation',
            'finder': f'findReqs;siteNumber=CX_45001,limit=100,selectedLocationsFacet={self.location_facet},sortBy=POSTING_DATES_DESC'
        }

        try:
            response = requests.get(self.api_url, headers=headers, params=params)

            if response.status_code != 200:
                logging.error(f"Oracle API returned {response.status_code}")
                return listings

            data = response.json()

            if 'items' not in data or not data['items']:
                logging.warning("No items found in Oracle API response")
                return listings

            jobs = data['items'][0].get('requisitionList', [])

            # IT-related keywords
            it_keywords = ['software', 'engineer', 'developer', 'data', 'cloud',
                          'it', 'technical', 'architect', 'devops', 'security',
                          'infrastructure', 'systems', 'technology', 'platform',
                          'gpu', 'solutions', 'ai', 'machine learning', 'database',
                          'oracle labs', 'intern']

            for job in jobs:
                job_id = job.get('Id', '')
                title = job.get('Title', '')
                location = job.get('PrimaryLocation', 'Switzerland')
                posted_date = job.get('PostedDate', '')

                # Filter for IT-related jobs
                title_lower = title.lower()
                category = job.get('JobCategoryDescription', '').lower()

                if (any(kw in title_lower for kw in it_keywords) or
                    any(kw in category for kw in it_keywords)):

                    # Build job URL
                    job_url = f"https://careers.oracle.com/jobs/#en/sites/jobsearch/job/{job_id}"

                    listing = OracleJobListing(
                        listing_id=job_id,
                        title=title,
                        location=location,
                        posted_date=posted_date,
                        link=job_url
                    )
                    listings.append(listing)

            self.current_listings = listings

        except Exception as e:
            logging.error(f"Error scraping Oracle jobs: {e}")

        return listings

    def _create_listing_from_dict(self, data: Dict[str, Any]) -> OracleJobListing:
        """Convert a dictionary back into an OracleJobListing object."""
        return OracleJobListing(
            listing_id=data["id"],
            title=data["title"],
            location=data["location"],
            posted_date=data["posted_date"],
            link=data["link"]
        )
