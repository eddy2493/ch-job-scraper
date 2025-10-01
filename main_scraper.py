import logging
import requests
from lib.google_scraper import GoogleJobScraper
from lib.meta_scraper import MetaJobScraper
from lib.nvidia_scraper import NvidiaJobScraper
from lib.apple_scraper import AppleJobScraper
from lib.microsoft_scraper import MicrosoftJobScraper
from lib.snap_scraper import SnapJobScraper
from lib.amazon_scraper import AmazonJobScraper
from lib.bkw_scraper import BKWJobScraper
from lib.lgtcp_scraper import LGTCPJobScraper
from lib.juliusbaer_scraper import JBJobScraper
from lib.lgt_scraper import LGTJobScraper
from lib.zkb_scraper import ZKBJobScraper
from lib.alpiq_scraper import AlpiqJobScraper
from lib.metgroup_scraper import METJobScraper
from lib.citadel_scraper import CitadelJobScraper
from lib.qrt_scraper import QRTJobScraper
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
    payload = {'chat_id': chat_id,
               'caption': caption, 'parse_mode': 'Markdown'}
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
scrapers = [GoogleJobScraper(), MetaJobScraper(), NvidiaJobScraper(
), AppleJobScraper(), MicrosoftJobScraper(), SnapJobScraper(), AmazonJobScraper(), BKWJobScraper(), LGTCPJobScraper(), JBJobScraper(), LGTJobScraper(), ZKBJobScraper(), AlpiqJobScraper(), METJobScraper(), CitadelJobScraper(), QRTJobScraper()]
for scraper in scrapers:
    logging.info(f"Starting scraper for {scraper.company}")
    try:
        old_jobs = scraper.load_previous_state()
        new_jobs = scraper.scrape()

        old_job_ids = {job.get_id(): job for job in old_jobs}
        new_job_ids = {job.get_id(): job for job in new_jobs}

        # Detect new and delisted jobs
        new_listings = [job for jid, job in new_job_ids.items() if jid not in old_job_ids]
        delisted_listings = [job for jid, job in old_job_ids.items() if jid not in new_job_ids]

        if new_listings or delisted_listings:
            scraper.save()
            logging.info(f"{scraper.company} - {len(new_listings)} new, {len(delisted_listings)} delisted jobs")

            # Build a single aggregated message
            message_parts = []

            if new_listings:
                message_parts.append("*NEW*")
                for job in new_listings:
                    message_parts.append(f"{job.title} - [Link]({job.link})")

            if delisted_listings:
                message_parts.append("\n*DELISTED*")
                for job in delisted_listings:
                    message_parts.append(f"{job.title}")

            aggregated_message = "\n".join(message_parts)

            # Send one message per Telegram account
            for acc in telegram_acc:
                if os.path.exists(scraper.logo_path):
                    send_telegram_photo_file(acc["token"], acc["chat_id"], scraper.logo_path, aggregated_message)
                else:
                    logging.warning(f"Logo not found for {scraper.company}, skipping Telegram message")

        else:
            logging.info(f"{scraper.company} - no changes")

        # Small delay to avoid overloading servers
        time.sleep(1)

    except Exception as e:
        logging.exception(f"{scraper.company} - Scraper Error: {e}")

        