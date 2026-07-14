"""
Test harness for all scrapers.

Runs each scraper's .scrape() and reports how many listings it returned,
WITHOUT loading creds, saving state, or sending anything to Telegram.

Usage:
    python3 test_scrapers.py                # test all scrapers
    python3 test_scrapers.py google meta    # test only matching scrapers (by company name)
"""

import logging
import sys
import time
import traceback

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
from lib.mobiliar_scraper import MobiliarJobScraper
from lib.redhat_scraper import RedHatJobScraper
from lib.databricks_scraper import DatabricksJobScraper
from lib.millennium_scraper import MillenniumJobScraper
from lib.vontobel_scraper import VontobelJobScraper
from lib.snb_scraper import SNBJobScraper
from lib.adobe_scraper import AdobeJobScraper
from lib.six_scraper import SIXJobScraper
from lib.deepmind_scraper import DeepMindJobScraper
from lib.anthropic_scraper import AnthropicJobScraper
from lib.thomsonreuters_scraper import ThomsonReutersJobScraper
from lib.squarepoint_scraper import SquarepointJobScraper
from lib.man_scraper import ManJobScraper
from lib.worldquant_scraper import WorldQuantJobScraper
from lib.openai_scraper import OpenAIJobScraper
from lib.palantir_scraper import PalantirJobScraper
from lib.ubs_scraper import UBSJobScraper

# Keep noise down; scrapers log their own errors at ERROR level.
logging.basicConfig(level=logging.WARNING, format='%(levelname)s - %(message)s')

SCRAPERS = [
    GoogleJobScraper, MetaJobScraper, NvidiaJobScraper, AppleJobScraper,
    MicrosoftJobScraper, SnapJobScraper, AmazonJobScraper, BKWJobScraper,
    LGTCPJobScraper, JBJobScraper, LGTJobScraper, ZKBJobScraper, AlpiqJobScraper,
    METJobScraper, CitadelJobScraper, QRTJobScraper, GetYourGuideJobScraper,
    IBMJobScraper, OracleJobScraper, AxpoJobScraper, BundesverwaltungJobScraper,
    IMCJobScraper, MathrixJobScraper, SBBJobScraper, SwisscomJobScraper,
    SwissReJobScraper, ZurichJobScraper, PostFinanceJobScraper, MobiliarJobScraper,
    RedHatJobScraper, DatabricksJobScraper, MillenniumJobScraper, VontobelJobScraper,
    SNBJobScraper, AdobeJobScraper, SIXJobScraper, DeepMindJobScraper,
    AnthropicJobScraper, ThomsonReutersJobScraper, SquarepointJobScraper,
    ManJobScraper, WorldQuantJobScraper, OpenAIJobScraper, PalantirJobScraper,
    UBSJobScraper,
]


def main():
    filters = [a.lower() for a in sys.argv[1:]]

    results = []
    for cls in SCRAPERS:
        scraper = cls()
        if filters and not any(f in scraper.company.lower() for f in filters):
            continue

        start = time.time()
        try:
            jobs = scraper.scrape()
            count = len(jobs) if jobs is not None else 0
            elapsed = time.time() - start
            if count > 0:
                status, detail = "OK", f"{count} jobs"
            else:
                status, detail = "WARN", "0 jobs returned"
            results.append((status, scraper.company, detail, elapsed))
            print(f"[{status:5}] {scraper.company:22} {detail:20} ({elapsed:.1f}s)")
        except Exception as e:  # noqa: BLE001 - we want to catch everything per scraper
            elapsed = time.time() - start
            results.append(("FAIL", scraper.company, f"{type(e).__name__}: {e}", elapsed))
            print(f"[FAIL ] {scraper.company:22} {type(e).__name__}: {e} ({elapsed:.1f}s)")
            traceback.print_exc()

        time.sleep(0.5)

    # Summary
    ok = [r for r in results if r[0] == "OK"]
    warn = [r for r in results if r[0] == "WARN"]
    fail = [r for r in results if r[0] == "FAIL"]

    print("\n" + "=" * 50)
    print(f"SUMMARY: {len(ok)} OK, {len(warn)} empty, {len(fail)} failed "
          f"(of {len(results)} tested)")
    if warn:
        print("  Empty (no jobs): " + ", ".join(r[1] for r in warn))
    if fail:
        print("  Failed:          " + ", ".join(r[1] for r in fail))

    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
