from lib.base_joblisting import JobListing
from lib.base_scraper import JobScraper
from typing import List, Dict, Any
import requests
import logging
import re
import json
 
class SnapJobListing(JobListing):
    def __init__(self, listing_id: str, title:str, location: str, link: str):
        self.id = listing_id
        self.title = title
        self.location = location
        self.link = link
        
    def get_id(self):
        return self.id

    def to_dict(self):
        return {"id": self.id, "title": self.title, "location": self.location, "link": self.link}

class SnapJobScraper(JobScraper):
    def __init__(self):
        super().__init__(company_name="Snap")
        self.logo_path = "lib/snap.png"
        self.url = 'https://careers.snap.com/api/jobs'
        self.cookies = {
            'sc-cookies-accepted': 'true',
            'sc-wcid': '0fbba1ca-8594-4480-8a77-2b3bae1a3822',
            'EssentialSession': 'true',
            'Preferences': 'true',
            'Performance': 'true',
            'Marketing': 'true',
            'blizzard_client_id': '480aa5a5-668e-432b-a013-012c2d6f7560:1727328476673',
            'blizzard_web_session_id': 'ivZL6k86S3GCEI1f',
        }
        self.headers = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.6',
            # 'cookie': 'sc-cookies-accepted=true; sc-wcid=0fbba1ca-8594-4480-8a77-2b3bae1a3822; EssentialSession=true; Preferences=true; Performance=true; Marketing=true; blizzard_client_id=480aa5a5-668e-432b-a013-012c2d6f7560:1727328476673; blizzard_web_session_id=ivZL6k86S3GCEI1f',
            'priority': 'u=1, i',
            'referer': 'https://careers.snap.com/jobs?location=Vienna',
            'sec-ch-ua': '"Brave";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Linux"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'sec-gpc': '1',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
        }
        self.params = {
            'location': 'Zurich',
            'role': '',
            'team': '',
            'type': '',
        }
        
    def scrape(self):
        response = requests.get('https://careers.snap.com/api/jobs', params=self.params, headers=self.headers, cookies=self.cookies)
        if response.status_code == 200:
            response = response.json()["body"]
        self.current_listings.extend([SnapJobListing(a["_source"]["id"], a["_source"]["title"], a["_source"]["primary_location"], a["_source"]["absolute_url"]) for a in response])
        return self.current_listings
        
    def _create_listing_from_dict(self, data: Dict[str, Any]) -> SnapJobListing:
        return SnapJobListing(data["id"], data["title"], data["location"], data["link"])
