import logging
import requests
import time
import json
import os
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
from lib.getyourguide_scraper import GetYourGuideJobScraper
from lib.ibm_scraper import IBMJobScraper
from lib.oracle_scraper import OracleJobScraper
from lib.axpo_scraper import AxpoJobScraper
from lib.bundesverwaltung_scraper import BundesverwaltungJobScraper
from lib.imc_scraper import IMCJobScraper
from lib.mathrix_scraper import MathrixJobScraper
from lib.sbb_scraper import SBBJobScraper
from lib.swisscom_scraper import SwisscomJobScraper
from lib.swissre_scraper import SwissReJobScraper
from lib.zurich_scraper import ZurichJobScraper
from lib.postfinance_scraper import PostFinanceJobScraper

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


def chunk_by_jobs(jobs_list, header="", max_length=1000):
    """Split a list of job lines into chunks that fit Telegram's caption/message limits."""
    chunks, current, length = [], [header] if header else [], len(header)

    for line in jobs_list:
        line_length = len(line) + 1  # newline
        if length + line_length > max_length:
            chunks.append("\n".join(current))
            current, length = [line], line_length
        else:
            current.append(line)
            length += line_length

    if current:
        chunks.append("\n".join(current))
    return chunks


def send_telegram_message(bot_token: str, chat_id: str, text: str):
    """Send a text message via Telegram without link previews."""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    r = requests.post(url, data=payload)
    if r.status_code != 200:
        logging.error(f"Telegram error {r.status_code}: {r.text}")



def send_telegram_photo_with_text(bot_token: str, chat_id: str, file_path: str, text_chunks: list):
    """Send a photo with first text chunk as caption, and extra chunks as messages."""
    url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
    files = {'photo': open(file_path, 'rb')}

    # First chunk as caption (if possible)
    caption = text_chunks[0] if text_chunks else None
    payload = {"chat_id": chat_id, "parse_mode": "Markdown"}
    if caption:
        payload["caption"] = caption

    r = requests.post(url, data=payload, files=files)
    if r.status_code != 200:
        logging.error(f"Telegram photo error {r.status_code}: {r.text}")
        return

    # Send remaining chunks as plain messages
    for chunk in text_chunks[1:]:
        send_telegram_message(bot_token, chat_id, chunk)


# --- Main Loop ---
scrapers = [GoogleJobScraper(), MetaJobScraper(), NvidiaJobScraper(),
            AppleJobScraper(), MicrosoftJobScraper(), SnapJobScraper(), AmazonJobScraper(),
            BKWJobScraper(), LGTCPJobScraper(), JBJobScraper(), LGTJobScraper(), ZKBJobScraper(),
            AlpiqJobScraper(), METJobScraper(), CitadelJobScraper(), QRTJobScraper(),
            GetYourGuideJobScraper(), IBMJobScraper(), OracleJobScraper(), AxpoJobScraper(),
            BundesverwaltungJobScraper(), IMCJobScraper(), MathrixJobScraper(), SBBJobScraper(),
            SwisscomJobScraper(), SwissReJobScraper(), ZurichJobScraper(),
            PostFinanceJobScraper()]
for scraper in scrapers:
    logging.info(f"Starting scraper for {scraper.company}")
    try:
        old_jobs = scraper.load_previous_state()
        new_jobs = scraper.scrape()

        if not new_jobs and old_jobs:
            logging.warning(f"{scraper.company} - scrape returned 0 results, skipping (possible maintenance)")
            continue

        old_job_ids = {job.get_id(): job for job in old_jobs}
        new_job_ids = {job.get_id(): job for job in new_jobs}

        new_listings = [job for jid, job in new_job_ids.items() if jid not in old_job_ids]
        delisted_listings = [job for jid, job in old_job_ids.items() if jid not in new_job_ids]

        if new_listings or delisted_listings:
            scraper.save()
            logging.info(f"{scraper.company} - {len(new_listings)} new, {len(delisted_listings)} delisted jobs")

            message_lines = []

            if new_listings:
                message_lines.append(f"*NEW* ({scraper.company})")
                for job in new_listings:
                    message_lines.append(f"{job.title} - [Link]({job.link})")

            if delisted_listings:
                message_lines.append(f"\n*DELISTED* ({scraper.company})")
                for job in delisted_listings:
                    message_lines.append(f"{job.title}")

            # Build chunks safely
            chunks = chunk_by_jobs(message_lines)

            # Send one message per Telegram account
            for acc in telegram_acc:
                if os.path.exists(scraper.logo_path):
                    send_telegram_photo_with_text(acc["token"], acc["chat_id"], scraper.logo_path, chunks)
                else:
                    for chunk in chunks:
                        send_telegram_message(acc["token"], acc["chat_id"], chunk)

        else:
            logging.info(f"{scraper.company} - no changes")

        time.sleep(1)

    except Exception as e:
        logging.exception(f"{scraper.company} - Scraper Error: {e}")
