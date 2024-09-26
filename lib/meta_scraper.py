from lib.base_joblisting import JobListing
from lib.base_scraper import JobScraper
from typing import List, Dict, Any
import requests
import logging
import re

class MetaJobListing(JobListing):
    def __init__(self, listing_id: str, title:str, locations: list[str], teams: list[str], sub_teams: list[str]):
        self.id = listing_id
        self.title = title
        self.locations = locations
        self.teams = teams
        self.sub_teams = sub_teams
        self.link = f"https://www.metacareers.com/jobs/{listing_id}/"
        
    def get_id(self):
        return self.id
    def generate_telegram_message(self):
        return f"{self.title} {self.id}\n{self.locations}\nTeams: {self.teams}\nSubTeams: {self.sub_teams}\n[Link]({self.link})"
        
    def to_dict(self):
        return {"id": self.id, "title": self.title, "locations": self.locations, "teams": self.teams, "sub_teams": self.sub_teams}

class MetaJobScraper(JobScraper):
    def __init__(self):
        super().__init__(company_name="Meta")
        self.url = "https://www.metacareers.com/graphql"
        self.logo_path = "lib/meta.png"
        self.headers = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.8',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://www.metacareers.com',
            'priority': 'u=1, i',
            'referer': 'https://www.metacareers.com/jobs/?q=&offices[0]=Geneva%2C%20Switzerland&offices[1]=Zurich%2C%20Switzerland',
            'sec-ch-ua': '"Brave";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Linux"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'sec-gpc': '1',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
            'x-asbd-id': '129477',
            'x-fb-friendly-name': 'CareersJobSearchResultsQuery',
            'x-fb-lsd': 'AVoOCtiGJrY',
        }
        self.data = {
            'variables': '{"search_input":{"q":"","divisions":[],"offices":["Geneva, Switzerland","Zurich, Switzerland"],"roles":[],"leadership_levels":[],"saved_jobs":[],"saved_searches":[],"sub_teams":[],"teams":[],"is_leadership":false,"is_remote_only":false,"sort_by_new":false,"page":1,"results_per_page":null}}',
            'server_timestamps': 'true',
            'doc_id': '9114524511922157',
        }
            
    def scrape(self) -> List[MetaJobListing]:
        response = requests.post(self.url,  headers=self.headers, data=self.data)
        
        if response.status_code == 200:
            current_listings = [MetaJobListing(l["id"], l["title"], l["locations"], l["teams"], l["sub_teams"]) for l in response.json()["data"]["job_search"]]
            self.current_listings.extend(current_listings)
            return self.current_listings
        return []
    
    def _create_listing_from_dict(self, data: Dict[str, Any]) -> MetaJobListing:
        return MetaJobListing(data["id"], data["title"], data["locations"], data["teams"], data["sub_teams"])
