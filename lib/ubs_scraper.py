from lib.base_joblisting import JobListing
from lib.base_scraper import JobScraper
from typing import List, Dict, Any
import requests
import logging


class UBSJobListing(JobListing):
    def __init__(self, listing_id: str, title: str, location: str, department: str, link: str):
        self.id = listing_id
        self.title = title
        self.location = location
        self.department = department
        self.link = link
        self.company = "UBS"

    def get_id(self) -> str:
        return self.id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "location": self.location,
            "department": self.department,
            "link": self.link
        }


class UBSJobScraper(JobScraper):
    """UBS runs on a Kenexa/IBM TalentGateway ("TgNewUI") behind CSRF + F5 anti-bot.

    The search endpoint needs a live session: we GET the search page first to obtain
    fresh cookies (tg_session, tg_rft, TS*), then reuse the tg_session value as the
    ``encryptedSessionValue`` field the search API requires. The linkId query returns
    all UBS jobs globally, so we filter to Switzerland via the formtext23 location field.
    """

    PARTNER_ID = "25008"
    SITE_ID = "5012"
    LINK_ID = "15231"
    MAX_PAGES = 20
    PAGE_SIZE = 50  # server default

    # Only keep IT, trading and portfolio-management roles. The job function lives in
    # the formtext21 field and appears in English or German depending on the posting.
    FUNCTION_KEYWORDS = (
        "information technology", "informationstechnologie",  # IT
        "trading", "handel",                                  # trading (e.g. "Sales and trading")
        "portfolio management", "portfoliomanagement",        # portfolio management
    )
    # UBS has no dedicated "quant" function category, so match quant roles by title.
    TITLE_KEYWORDS = ("quant",)  # Quant, Quantitative

    BOOTSTRAP_URL = (
        "https://jobs.ubs.com/TGnewUI/Search/home/HomeWithPreLoad"
        f"?partnerid=25008&siteid=5012&PageType=searchResults&SearchType=linkquery&LinkID=15231"
    )
    SEARCH_URL = "https://jobs.ubs.com/TgNewUI/Search/Ajax/ProcessSortAndShowMoreJobs"

    def __init__(self):
        super().__init__(company_name="UBS")
        self.logo_path = "lib/ubs.png"
        self.user_agent = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                           "(KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36")

    def _payload(self, page: int, enc_session: str) -> Dict[str, Any]:
        return {
            "partnerId": self.PARTNER_ID,
            "siteId": self.SITE_ID,
            "keyword": "",
            "location": "",
            "keywordCustomSolrFields": "FORMTEXT2,FORMTEXT21,AutoReq,Department,JobTitle",
            "locationCustomSolrFields": "FORMTEXT2,FORMTEXT23,Location",
            "linkId": self.LINK_ID,
            "Latitude": 0,
            "Longitude": 0,
            "facetfilterfields": {"Facet": []},
            "powersearchoptions": {"PowerSearchOption": [
                {"VerityZone": "FORMTEXT2", "Type": "multi-select", "OptionCodes": []},
                {"VerityZone": "FORMTEXT21", "Type": "multi-select", "OptionCodes": []},
                {"VerityZone": "Department", "Type": "select", "OptionCodes": []},
                {"VerityZone": "FORMTEXT23", "Type": "multi-select", "OptionCodes": []},
                {"VerityZone": "LastUpdated", "Type": "date", "Value": None},
            ]},
            "SortType": "LastUpdated",
            "pageNumber": page,
            "encryptedSessionValue": enc_session,
        }

    @staticmethod
    def _questions_to_dict(job: Dict[str, Any]) -> Dict[str, str]:
        result = {}
        for q in job.get("Questions", []):
            name = q.get("QuestionName")
            if name:
                result[name] = q.get("Value") or q.get("ActualValueFromSolar") or ""
        return result

    def scrape(self) -> List[UBSJobListing]:
        session = requests.Session()
        session.headers.update({"User-Agent": self.user_agent})

        try:
            # Bootstrap a fresh session (cookies + CSRF/session token).
            boot = session.get(self.BOOTSTRAP_URL, timeout=25)
            boot.raise_for_status()
            enc_session = session.cookies.get("tg_session")
            if not enc_session:
                logging.error("UBS - no tg_session cookie after bootstrap, skipping")
                return []

            headers = {
                "Content-Type": "application/json;charset=UTF-8",
                "Accept": "application/json, text/plain, */*",
                "Origin": "https://jobs.ubs.com",
                "Referer": self.BOOTSTRAP_URL,
            }

            listings = []
            seen_ids = set()

            # The API is 1-indexed: pageNumber 1 -> offset 0, 2 -> offset 50, etc.
            # (pageNumber 0 aliases to page 1, so starting at 0 would just duplicate it.)
            for page in range(1, self.MAX_PAGES + 1):
                resp = session.post(self.SEARCH_URL, headers=headers,
                                    json=self._payload(page, enc_session), timeout=25)
                if resp.status_code != 200:
                    logging.error(f"UBS search returned {resp.status_code} on page {page}")
                    break

                data = resp.json()
                jobs = data.get("Jobs", {}).get("Job", [])
                total = data.get("JobsCount", 0)
                if not jobs:
                    break

                new_on_page = 0
                for job in jobs:
                    qs = self._questions_to_dict(job)
                    reqid = str(qs.get("reqid", ""))
                    if not reqid or reqid in seen_ids:
                        continue
                    seen_ids.add(reqid)
                    new_on_page += 1

                    location = qs.get("formtext23", "").strip()
                    loc_lower = location.lower()
                    if "schweiz" not in loc_lower and "switzerland" not in loc_lower:
                        continue

                    title = qs.get("jobtitle", "").strip()
                    function = qs.get("formtext21", "").strip()
                    fn_lower = function.lower()
                    keep = (any(kw in fn_lower for kw in self.FUNCTION_KEYWORDS)
                            or any(kw in title.lower() for kw in self.TITLE_KEYWORDS))
                    if not keep:
                        continue

                    listings.append(UBSJobListing(
                        listing_id=reqid,
                        title=title,
                        location=location,
                        department=function or qs.get("department", "").strip(),
                        link=job.get("Link", ""),
                    ))

                if new_on_page == 0 or len(seen_ids) >= total:
                    break

            self.current_listings = listings
            return listings

        except Exception as e:
            logging.error(f"Error scraping UBS jobs: {e}")
            return []

    def _create_listing_from_dict(self, data: Dict[str, Any]) -> UBSJobListing:
        return UBSJobListing(
            listing_id=data["id"],
            title=data["title"],
            location=data["location"],
            department=data["department"],
            link=data["link"]
        )
