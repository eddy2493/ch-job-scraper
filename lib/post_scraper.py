from lib.base_joblisting import JobListing
from lib.base_scraper import JobScraper
from typing import List, Dict, Any
from html import unescape
import requests
import logging


class PostJobListing(JobListing):
    def __init__(self, listing_id: str, title: str, link: str, department: str, city: str, pensum: str):
        self.id = listing_id
        self.title = title
        self.link = link
        self.department = department
        self.city = city
        self.pensum = pensum

    def get_id(self) -> str:
        return self.id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "link": self.link,
            "department": self.department,
            "city": self.city,
            "pensum": self.pensum,
        }


class PostJobScraper(JobScraper):
    # job.post.ch is a shared tenant: brandUrl is PostKG (Swiss Post), PostFinance, or
    # "default" (PostAuto / logistics / real estate). Skip PostFinance so we never
    # duplicate PostFinanceJobScraper; excluding it (rather than requiring PostKG) keeps
    # a Post IT role filed under "default" in scope.
    SKIP_BRAND = "PostFinance"

    # A job is only returned under the locales it was published in -- 11 of Post's IT
    # roles are English-only and appear in no other feed -- so every locale gets queried
    # and results are deduped by id.
    LOCALES = ["de_DE", "en_US", "fr_FR", "it_IT"]

    # filter1 is localised: "Informatik und Digital Services" (de),
    # "Informatics and digital business" (en), "Informatique" (fr), "Informatica" (it).
    # This one substring matches all of them.
    FILTER_KEYWORD = "Informati"

    # Post's IT arm runs a Budapest dev centre, and its roles are posted in English on the
    # same board -- hence the en-only postings. Keep only jobs with at least one CH
    # location; the last "|"-field of jobLocationShort is the ISO country code, e.g.
    # "Morges|Vaud|VD|Switzerland|CHE " vs "Budapest|Hungary|HUN ". Checking every entry
    # (not just the first) keeps hybrid roles like "Budapest|HUN" + "hybrid|CHE".
    COUNTRY_CODE = "CHE"
    MAX_PAGES = 20

    def __init__(self):
        super().__init__(company_name="Post")
        self.logo_path = "lib/post.png"
        self.url = "https://job.post.ch/services/recruiting/v1/jobs"
        self.headers = {
            "accept": "*/*",
            "content-type": "application/json",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
            "origin": "https://job.post.ch",
            "referer": "https://job.post.ch/search?locale=de_DE&searchResultView=LIST",
        }

    def _payload(self, locale: str, page: int) -> Dict[str, Any]:
        return {"locale": locale, "pageNumber": page, "sortBy": "date"}

    def scrape(self) -> List[PostJobListing]:
        seen_ids = set()
        listings = []

        for locale in self.LOCALES:
            # Paginate on a per-locale count: totalJobs is per-locale, and seen_ids is
            # global (a job published in both de and en shows up twice), so the two must
            # not share bookkeeping or later locales terminate early.
            locale_count = 0

            for page in range(self.MAX_PAGES):
                try:
                    response = requests.post(
                        self.url, headers=self.headers, json=self._payload(locale, page)
                    )
                    response.raise_for_status()
                    data = response.json()
                except Exception as e:
                    logging.error(f"Post scrape failed ({locale}, page {page}): {e}")
                    break

                results = data.get("jobSearchResult", [])
                if not results:
                    break
                locale_count += len(results)

                for item in results:
                    job = item.get("response", {})
                    listing_id = str(job.get("id", ""))
                    if not listing_id or listing_id in seen_ids:
                        continue
                    seen_ids.add(listing_id)

                    brand = job.get("brandUrl") or "default"
                    if brand == self.SKIP_BRAND:
                        continue

                    category = (job.get("filter1") or [""])[0]
                    if self.FILTER_KEYWORD not in category:
                        continue

                    locations = job.get("jobLocationShort", [])
                    if not any(loc.split("|")[-1].strip() == self.COUNTRY_CODE for loc in locations):
                        continue

                    title = job.get("unifiedStandardTitle", "")
                    url_title = unescape(job.get("urlTitle", ""))
                    link = f"https://job.post.ch/{brand}/job/{url_title}/{listing_id}-{locale}"

                    # "Bern|Bern|BE|Schweiz|CHE " -> "Bern"
                    cities = [loc.split("|")[0].strip() for loc in locations]
                    city = ", ".join(dict.fromkeys(c for c in cities if c))

                    wmin = (job.get("cust_WorkingTimeMin") or [""])[0]
                    wmax = (job.get("cust_WorkingTimeMax") or [""])[0]
                    pensum = f"{wmin}-{wmax}%" if wmin and wmax else (f"{wmin or wmax}%" if (wmin or wmax) else "")

                    listings.append(PostJobListing(listing_id, title, link, category, city, pensum))

                if locale_count >= data.get("totalJobs", 0):
                    break

        self.current_listings = listings
        return listings

    def _create_listing_from_dict(self, data: Dict[str, Any]) -> PostJobListing:
        return PostJobListing(
            data["id"], data["title"], data["link"],
            data["department"], data["city"], data["pensum"],
        )
