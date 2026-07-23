from lib.base_joblisting import JobListing
from lib.base_scraper import JobScraper
from typing import List, Dict, Any
import requests
import logging
import json
import re


class AdobeJobListing(JobListing):
    def __init__(self, listing_id: str, title: str, location: str, link: str):
        self.id = listing_id
        self.title = title
        self.location = location
        self.link = link

    def get_id(self) -> str:
        return self.id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "location": self.location,
            "link": self.link
        }


class AdobeJobScraper(JobScraper):
    def __init__(self):
        super().__init__(company_name="Adobe")
        self.logo_path = "lib/adobe.png"
        self.url = "https://careers.adobe.com/us/en/search-results?qcountry=Switzerland"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
        }

    # Adobe serves 10 results per page and returns a shifting subset of the matches
    # on every request, so a single page misses listings at random. Paginate with
    # "from" (NOT "s=1" - that silently drops the qcountry filter) and repeat the
    # sweep until every match has been seen.
    MAX_SWEEPS = 3

    def scrape(self) -> List[AdobeJobListing]:
        listings = []

        try:
            jobs_by_id, total = {}, None

            for _ in range(self.MAX_SWEEPS):
                offset, page_size = 0, 10

                while True:
                    response = requests.get(self.url, headers=self.headers,
                                            params={"from": offset}, timeout=15)
                    if response.status_code != 200:
                        logging.error(f"Adobe returned {response.status_code} at offset {offset}")
                        return []

                    if total is None:
                        total = self._extract_total(response.text)

                    page = self._extract_jobs(response.text)
                    if not page:
                        break

                    for job in page:
                        jobs_by_id[job.get('jobId', '')] = job

                    if offset == 0:
                        page_size = len(page)
                    offset += page_size
                    if total is None or offset >= total:
                        break

                if total is None or len(jobs_by_id) >= total:
                    break

            # A short read means the shuffle hid listings from us - reporting the
            # partial set would raise false delistings, so skip this run instead.
            if total is not None and len(jobs_by_id) < total:
                logging.warning(f"Adobe: only got {len(jobs_by_id)} of {total} listings, skipping")
                return []

            for job in jobs_by_id.values():
                if job.get('country', '') != 'Switzerland':
                    continue

                job_url = f"https://careers.adobe.com/us/en/job/{job.get('jobId', '')}"
                listings.append(AdobeJobListing(
                    listing_id=job.get('jobId', ''),
                    title=job.get('title', ''),
                    location=f"{job.get('city', '')}, {job.get('country', '')}",
                    link=job_url
                ))

            self.current_listings = listings

        except Exception as e:
            logging.error(f"Error scraping Adobe jobs: {e}")

        return listings

    def _extract_total(self, html: str) -> int:
        """Total number of matches reported by the search page."""
        m = re.search(r'"totalHits":(\d+)', html)
        return int(m.group(1)) if m else None

    def _extract_jobs(self, html: str) -> list:
        """Extract jobs array from embedded Phenom SSR data."""
        idx = html.find('"jobs":[{')
        if idx == -1:
            return []

        start = idx + len('"jobs":')
        bracket = 0
        i = start
        while i < len(html):
            c = html[i]
            if c == '[':
                bracket += 1
            elif c == ']':
                bracket -= 1
                if bracket == 0:
                    end = i + 1
                    break
            elif c == '"':
                i += 1
                while i < len(html) and html[i] != '"':
                    if html[i] == '\\':
                        i += 1
                    i += 1
            i += 1
        else:
            return []

        return json.loads(html[start:end])

    def _create_listing_from_dict(self, data: Dict[str, Any]) -> AdobeJobListing:
        return AdobeJobListing(
            listing_id=data["id"],
            title=data["title"],
            location=data["location"],
            link=data["link"]
        )
