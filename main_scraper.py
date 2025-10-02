import logging
import requests
import time
import json
import os
from datetime import datetime, timedelta
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
from lib.mathrix_scraper import MathrixJobScraper
from lib.imc_scraper import IMCJobScraper

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

# Grace period: only report jobs as delisted after they've been missing for this long
DELISTING_GRACE_PERIOD_HOURS = 4


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
scrapers = [GoogleJobScraper(), MetaJobScraper(), NvidiaJobScraper(
), AppleJobScraper(), MicrosoftJobScraper(), SnapJobScraper(), AmazonJobScraper(), BKWJobScraper(), LGTCPJobScraper(), JBJobScraper(), LGTJobScraper(), ZKBJobScraper(), AlpiqJobScraper(), METJobScraper(), CitadelJobScraper(), QRTJobScraper(), GetYourGuideJobScraper(), IBMJobScraper(), OracleJobScraper(), AxpoJobScraper(), MathrixJobScraper(), IMCJobScraper()]
for scraper in scrapers:
    logging.info(f"Starting scraper for {scraper.company}")
    try:
        old_jobs, last_seen_times = scraper.load_previous_state()
        new_jobs = scraper.scrape()

        current_time = datetime.now()
        current_time_str = current_time.isoformat()

        old_job_ids = {job.get_id(): job for job in old_jobs}
        new_job_ids = {job.get_id(): job for job in new_jobs}

        # Find new listings
        new_listings = [job for jid, job in new_job_ids.items() if jid not in old_job_ids]

        # Update last_seen times for all jobs that are currently present
        updated_last_seen = {}
        for jid in new_job_ids.keys():
            # If job exists, update its last_seen time
            updated_last_seen[jid] = current_time_str

        # For jobs that disappeared, keep their last_seen time from before
        for jid in old_job_ids.keys():
            if jid not in new_job_ids and jid in last_seen_times:
                updated_last_seen[jid] = last_seen_times[jid]

        # Find delisted jobs that have been missing for more than the grace period
        delisted_listings = []
        grace_period = timedelta(hours=DELISTING_GRACE_PERIOD_HOURS)

        for jid, job in old_job_ids.items():
            if jid not in new_job_ids:
                # Job is missing - check if it's been missing long enough
                last_seen_str = last_seen_times.get(jid, current_time_str)
                try:
                    last_seen = datetime.fromisoformat(last_seen_str)
                    time_since_last_seen = current_time - last_seen

                    if time_since_last_seen > grace_period:
                        # Job has been missing for more than grace period
                        delisted_listings.append(job)
                        # Remove from last_seen tracking since we're reporting it as delisted
                        if jid in updated_last_seen:
                            del updated_last_seen[jid]
                except (ValueError, TypeError):
                    # If we can't parse the timestamp, treat as newly missing
                    pass

        if new_listings or delisted_listings:
            scraper.save(last_seen_times=updated_last_seen)
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
            # Even if no changes to report, still save to update last_seen times
            scraper.save(last_seen_times=updated_last_seen)
            logging.info(f"{scraper.company} - no changes")

        time.sleep(1)

    except Exception as e:
        logging.exception(f"{scraper.company} - Scraper Error: {e}")
