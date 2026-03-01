import time
from typing import Dict, Any, Optional

from .base_scraper import BaseBankScraper
from .biat_inspects import BIAT_INSPECTS
from .biat_inspects import common
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class BIATScraper(BaseBankScraper):
    """
    Scraper minimal: la logique spécifique est dans src/scrapers/biat_inspects/inspect_*.py
    """

    def __init__(self, headless: bool = True):
        super().__init__(headless)
        self.inspect = BIAT_INSPECTS["CREDIMEDIA"]
        self.base_url = self.inspect.URL
        self.current_profile: Optional[Dict[str, Any]] = None

    def _pick_inspect(self, profile: Dict[str, Any]):
        # override manuel possible
        if profile.get("biat_simulator") in BIAT_INSPECTS:
            return BIAT_INSPECTS[profile["biat_simulator"]]

        loan_type = (profile.get("loan_type") or "").upper()
        if loan_type == "AUTO":
            return BIAT_INSPECTS["CREDIAUTO"]
        if loan_type == "IMMO":
            return BIAT_INSPECTS["BIATIMMO"]
        # défaut conso
        return BIAT_INSPECTS["CREDIMEDIA"]

    def run(self, playwright, profile: Dict[str, Any]) -> Dict[str, Any]:
        self.inspect = self._pick_inspect(profile)
        self.base_url = self.inspect.URL
        profile["biat_simulator"] = self.inspect.KEY
        return super().run(playwright, profile)

    def navigate(self):
        logger.info(f"Navigating BIAT {self.inspect.KEY}: {self.base_url}")
        self.page.goto(self.base_url, wait_until="networkidle", timeout=60000)
        time.sleep(0.6)

    def fill_form(self, profile: Dict[str, Any]):
        self.current_profile = profile
        logger.info(f"Filling BIAT {self.inspect.KEY} ...")
        self.inspect.fill(self.page, profile)

    def submit_and_wait(self):
        logger.info(f"Submitting BIAT {self.inspect.KEY} ...")
        self.inspect.submit_and_wait(self.page)

    def extract_result(self) -> Dict[str, Any]:
        logger.info(f"Extracting BIAT {self.inspect.KEY} result ...")

        result = {
            "bank_name": "BIAT",
            "result_status": "ERROR",
            "monthly_payment": None,
            "interest_rate": 0.0,
            "details": "",
        }

        # extra details (ex: conditions)
        try:
            det = self.inspect.extra_details(self.page)
            if det:
                result["details"] = det
        except Exception:
            pass

        # monthly
        try:
            self.page.wait_for_selector("#remb_mensuel", state="attached", timeout=20000)
            txt = (self.page.text_content("#remb_mensuel") or "").strip()
            monthly = common.parse_monthly_payment(txt)
            if monthly is None:
                result["details"] = (result["details"] + " | cannot parse monthly").strip(" |")
                return result

            result["monthly_payment"] = monthly
            result["result_status"] = "ELIGIBLE"

            # interest rate (implicite)
            if self.current_profile:
                P, n = self.inspect.principal_and_months(self.current_profile)
                if P and n:
                    result["interest_rate"] = common.estimate_annual_rate_percent(float(P), int(n), float(monthly))

        except Exception as e:
            result["details"] = (result["details"] + f" | {e}").strip(" |")

        return result