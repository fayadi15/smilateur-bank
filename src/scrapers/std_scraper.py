from typing import Dict, Any, Optional

from .base_scraper import BaseBankScraper
from .std_inspects import STD_INSPECTS
from .std_inspects import common
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class STDScraper(BaseBankScraper):
    def __init__(self, headless: bool = True):
        super().__init__(headless)
        self.inspect = STD_INSPECTS["CREDIT_IMMOBILIER"]
        self.base_url = self.inspect.URL
        self.current_profile: Optional[Dict[str, Any]] = None

    def _pick_inspect(self, profile: Dict[str, Any]):
        if profile.get("std_simulator") in STD_INSPECTS:
            return STD_INSPECTS[profile["std_simulator"]]

        loan_type = (profile.get("loan_type") or "").upper()
        if loan_type == "AUTO":
            return STD_INSPECTS["CREDIT_AUTO"]
        if loan_type == "IMMO":
            return STD_INSPECTS["CREDIT_IMMOBILIER"]
        return STD_INSPECTS["CREDIT_CONSO"]

    def run(self, playwright, profile: Dict[str, Any]) -> Dict[str, Any]:
        self.inspect = self._pick_inspect(profile)
        self.base_url = self.inspect.URL
        profile["std_simulator"] = self.inspect.KEY
        return super().run(playwright, profile)

    def navigate(self):
        logger.info(f"Navigating STB {self.inspect.KEY}: {self.base_url}")
        self.page.goto(self.base_url, wait_until="networkidle", timeout=60000)

    def fill_form(self, profile: Dict[str, Any]):
        self.current_profile = profile
        logger.info(f"Filling STB {self.inspect.KEY} ...")
        self.inspect.fill(self.page, profile)

    def submit_and_wait(self):
        logger.info(f"Submitting STB {self.inspect.KEY} ...")
        self.inspect.submit_and_wait(self.page)

    def extract_result(self) -> Dict[str, Any]:
        logger.info(f"Extracting STB {self.inspect.KEY} ...")

        result = {
            "bank_name": "STB",
            "result_status": "ERROR",
            "monthly_payment": None,
            "interest_rate": 0.0,
            "details": "",
        }

        salaire_s, capacite_s, msg, mens_s = common.get_result_fields(self.page)
        msg_norm = common.norm_text(msg)

        monthly = common.parse_float_fr(mens_s)
        result["monthly_payment"] = monthly
        result["details"] = msg

        if "eligible" in msg_norm:
            result["result_status"] = "ELIGIBLE"
        else:
            result["result_status"] = "REFUSED"

        if self.current_profile:
            self.current_profile["std_res_salaire"] = salaire_s
            self.current_profile["std_res_capacite"] = capacite_s

        if self.current_profile and monthly:
            P, n = self.inspect.principal_and_months(self.current_profile)
            if P and n:
                result["interest_rate"] = common.estimate_annual_rate_percent(float(P), int(n), float(monthly))

        return result