#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Sep 26 08:36:40 2024

@author: gnms
"""

from lib.base_joblisting import JobListing
from lib.base_scraper import JobScraper
from typing import List, Dict, Any
import requests
import logging
import re
import json
 
class AmazonJobListing(JobListing):
    def __init__(self, listing_id: str, title:str, location: str, link: str):
        self.id = listing_id
        self.title = title
        self.location = location
        self.link = link
        
    def get_id(self):
        return self.id

    def generate_telegram_message(self):
        return f"{self.title} {self.id}\n{self.location}\n[Link]({self.link})"

    def to_dict(self):
        return {"id": self.id, "title": self.title, "location": self.location, "link": self.link}

class AmazonJobScraper(JobScraper):
    def __init__(self):
        super().__init__(company_name="Amazon")
        self.logo_path = "lib/amazon.png"
        self.url = 'https://amazon.jobs/de/search.json'
        self.params = {
            'radius': '24km',
            'facets[]': [
                'normalized_country_code', 'normalized_state_name', 'normalized_city_name',
                'location', 'business_category', 'category', 'schedule_type_id',
                'employee_class', 'normalized_location', 'job_function_id',
                'is_manager', 'is_intern'
            ],
            'offset': 0,  # Start from the first page
            'result_limit': 10,  # Number of results per page
            'sort': 'relevant',
            'location[]': 'zurich-switzerland'
        }
        
    def scrape(self):
        all_jobs = []
        total_hits = None  # Will store the total number of results once retrieved

        headers = {
            "Accept-Encoding": "gzip, deflate, br",  # prevent zstd
            "User-Agent": "Mozilla/5.0 (compatible; JobScraper/1.0)"
        }

        while True:
            response = requests.get(self.url, params=self.params, headers=headers, timeout=20)
            try:
                data = response.json()
            except Exception as e:
                logging.error(f"{self.company} - Failed to parse JSON: {e}")
                break

            # Check if response contains jobs
            if 'jobs' in data:
                all_jobs.extend(data['jobs'])
            else:
                break  # Exit if no jobs found

            # Check total number of hits (this is only needed for the first request)
            if total_hits is None:
                total_hits = data.get('hits', 0)

            # Increment the offset for the next request (pagination)
            self.params['offset'] += self.params['result_limit']

            # Break when all jobs are fetched
            if len(all_jobs) >= total_hits:
                break

        self.current_listings.extend([
            AmazonJobListing(
                a["id_icims"],
                a["title"],
                a["normalized_location"],
                "https://amazon.jobs" + a["job_path"]
            )
            for a in all_jobs
        ])
        return self.current_listings
        
    def _create_listing_from_dict(self, data: Dict[str, Any]) -> AmazonJobListing:
        return AmazonJobListing(data["id"], data["title"], data["location"], data["link"])
