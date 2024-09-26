from lib.base_joblisting import JobListing
from lib.base_scraper import JobScraper
from typing import List, Dict, Any
import requests
import logging
import re

class NvidiaJobListing(JobListing):
    def __init__(self, listing_id: str, title:str, locations: str, link: str):
        self.id = listing_id
        self.title = title
        self.locations = locations
        self.link = link
        self.location_from_link = self.extract_location_from_url(link)
    def extract_location_from_url(self, url):
        # Regex pattern to extract the location and job title from the URL
        pattern = r'/job/([^/]+)/'
        
        match = re.search(pattern, url)
        
        if match:
            # Extracted location (and job title)
            location = match.group(1).replace('-', ' ')
            return location
        else:
            return None
    def get_id(self):
        return self.id
    
    def generate_telegram_message(self):
        return f"{self.title} {self.id}\n{self.locations}\nLocation from Link: {self.location_from_link}\n[Link]({self.link})"
            
    def to_dict(self):
        return {"id": self.id, "title": self.title, "locations": self.locations, "link": self.link, "location_from_link": self.location_from_link}
       
class NvidiaJobScraper(JobScraper):
    def __init__(self):
        super().__init__(company_name="Nvidia")
        self.logo_path = "lib/nvidia.png"
        self.url = 'https://nvidia.wd5.myworkdayjobs.com/wday/cxs/nvidia/NVIDIAExternalCareerSite/jobs'
        self.json_data = {
            'appliedFacets': {
                'locationHierarchy1': [
                    '2fcb99c455831013ea52e9ef1a0032ba',  # Example location ID (Switzerland)
                ],
            },
            'limit': 20,  # The number of jobs per request (page size)
            'offset': 0,  # The starting point for the results
            'searchText': '',
        }
        
        
    def scrape(self):
        all_jobs = []
        total_jobs = None
        offset = 0
        limit = self.json_data['limit']
    
        while total_jobs is None or offset < total_jobs:
            # Update the offset for pagination
            self.json_data['offset'] = offset
    
            # Send the request
            response = requests.post(self.url, json=self.json_data)
            
            data = response.json()
    
            if total_jobs is None:
                # Set total_jobs from the first response
                total_jobs = data.get('total', 0)
    
            # Extract job postings
            jobs = data.get('jobPostings', [])
            for job in jobs:
                job_info = {
                    'title': job.get('title'),
                    'locations': job.get('locationsText'),
                    'posted_on': job.get('postedOn'),
                    'job_id': job.get('bulletFields', [None])[0],
                    'job_url': f"https://nvidia.wd5.myworkdayjobs.com{job.get('externalPath')}",
                }
                all_jobs.append(job_info)
            
            # Update the offset to move to the next page
            offset += limit
        self.current_listings.extend([NvidiaJobListing(b["job_id"], b["title"], b["locations"], b["job_url"]) for b in all_jobs])    
        return self.current_listings
    def _create_listing_from_dict(self, data: Dict[str, Any]) -> NvidiaJobListing:
        return NvidiaJobListing(data["id"], data["title"], data["locations"], data["link"])


