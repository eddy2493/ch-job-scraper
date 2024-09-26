import logging
import requests
from lib.google_scraper import GoogleJobScraper
from lib.meta_scraper import MetaJobScraper
from lib.nvidia_scraper import NvidiaJobScraper
from lib.apple_scraper import AppleJobScraper
from lib.microsoft_scraper import MicrosoftJobScraper
from lib.snap_scraper import SnapJobScraper
from lib.amazon_scraper import AmazonJobScraper
import time
import json
import os

# Change the working directory to the script's directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scraper.log"),
        logging.StreamHandler()
    ]
)

with open('creds.txt', 'r') as file:
    telegram_acc = json.load(file)
def send_telegram_photo_file(bot_token: str, chat_id: str, file_path: str, caption: str = None):
    url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
    payload = {'chat_id': chat_id, 'caption': caption, 'parse_mode': 'Markdown'}
    files = {'photo': open(file_path, 'rb')}
    
    response = requests.post(url, data=payload, files=files)
    
    if response.status_code == 200:
        pass
    elif response.status_code == 429:
        time.sleep(2)
        send_telegram_photo_file(bot_token, chat_id, file_path, caption)
    else:
        logging.error("Unable to send Update via Telegram")

# Set up logging configuration
scrapers = [GoogleJobScraper(), MetaJobScraper(), NvidiaJobScraper(), AppleJobScraper(), MicrosoftJobScraper(), SnapJobScraper(), AmazonJobScraper()]

for scraper in scrapers:
    
    old_jobs = scraper.load_previous_state()
    new_jobs = scraper.scrape()
    
    new_job_ids = {new_job.get_id(): new_job for new_job in new_jobs}
    old_job_ids = {old_job.get_id(): old_job for old_job in old_jobs}
    
    # Detect new listings
    new_listings = [new_job for new_job_id,
                    new_job in new_job_ids.items() if new_job_id not in old_job_ids]
    
    # Detect delisted listings
    delisted_listings = [old_job for old_job_id,
                         old_job in old_job_ids.items() if old_job_id not in new_job_ids]
    
    
    if delisted_listings or new_listings:
        scraper.save()
    else:
        logging.info(f"{scraper.company} - no changes")
        
    for delisted in delisted_listings:
        for acc in telegram_acc:
            send_telegram_photo_file(acc["token"], acc["chat_id"], scraper.logo_path, f"delisted \n"+delisted.generate_telegram_message())
    
    for new in new_listings:
        for acc in telegram_acc:
            send_telegram_photo_file(acc["token"], acc["chat_id"], scraper.logo_path, f"NEW \n"+new.generate_telegram_message())

