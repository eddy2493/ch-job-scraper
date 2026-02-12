from lib.base_joblisting import JobListing
from lib.base_scraper import JobScraper
from typing import List, Dict, Any
from bs4 import BeautifulSoup
import requests
import logging
import re

class GoogleJobListing(JobListing):
    def __init__(self, listing_id: str, title: str, min_quali: str, pref_quali: str, link: str, location: str, division: str, position):
        self.id = listing_id
        self.title = title
        self.min_qualifications = min_quali
        self.preferred_qualifications = pref_quali
        self.link = link
        self.company = "Google"
        self.location = location
        self.division = division
        self.position = position

    def get_id(self) -> str:
        return self.id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "min_quali": self.min_qualifications,
            "pref_quali": self.preferred_qualifications,
            "link": self.link,
            "company": self.company,
            "location": self.location,
            "division": self.division,
            "position": self.position
        }


class GoogleJobScraper(JobScraper):
    def __init__(self):
        super().__init__(company_name="Google")
        self.url = "https://www.google.com/about/careers/applications/jobs/results?location=Switzerland&"
        self.logo_path = "lib/google.png"

    def scrape(self) -> List[GoogleJobListing]:
        # Your scraping logic
        
        i = 1
        while(True):
            response = requests.get(self.url+"page="+str(i))
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                divs = soup.find_all('div', class_='Ln1EL')
                if len(divs)>0:
                    self.current_listings.extend([self.extract_description(div) for div in divs])
                    i+=1
                else:
                    break
            else:
                logging.error("Could not scrape Google")
                
        return self.current_listings

    def extract_description(self, element: Any) -> GoogleJobListing:
        # Extract information from the HTML element
        link = "https://www.google.com/about/careers/applications/"+element.find('a', class_='WpHeLc')['href']
        listing_id = re.search(r'jobs/results/(\d+)-', link).group(1)
        title = element.find('h3', class_='QJPWVe').get_text()
        min_quali = [li.get_text(strip=True) for li in element.find('h4', string='Minimum qualifications').find_next('ul').find_all('li')] 
        
        div = element.find('div', class_='op1BBf')

# Create a dictionary to store the results
        result = {}
        
        # Define the icons and their corresponding labels to extract
        icons = {
            "corporate_fare": "Company",
            "place": "Location",
            "bar_chart": "Position"
        }
        
        for icon, label in icons.items():
            # Find the <i> tag with the specific icon name
            icon_tag = div.find('i', text=icon)
            if icon_tag:
                if icon == "place":
                    # Collect all the spans containing location text by looping through siblings
                    location_container = icon_tag.find_next_sibling('span')
                    locations = []
                    while location_container:
                        locations.append(location_container.text.strip())
                        location_container = location_container.find_next_sibling('span')
                    result[label] = ' '.join(locations)
                elif icon == "bar_chart":
                    # bar_chart is nested in a button/tooltip widget
                    wvstab = div.find('span', class_='wVSTAb')
                    if wvstab:
                        result[label] = wvstab.text.strip()
                else:
                    # For other icons, get the next sibling <span> text
                    next_span = icon_tag.find_next_sibling('span')
                    if next_span:
                        result[label] = next_span.text.strip()

        
        pref_quali = []
        pref_qual_section = element.find('h4', string='Preferred qualifications')
        if pref_qual_section:
            pref_quali = [li.get_text(strip=True) for li in pref_qual_section.find_next('ul').find_all('li')]

        return GoogleJobListing(listing_id, title, min_quali, pref_quali, link, result.get("Location", ""), result.get("Company", ""), result.get("Position", ""))

    def _create_listing_from_dict(self, data: Dict[str, Any]) -> GoogleJobListing:
        return GoogleJobListing(data["id"], data["title"], data["min_quali"], data["pref_quali"], data["link"], data["location"], data["division"], data["position"])
