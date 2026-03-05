from typing import Dict, Any, Optional

from .base_scraper import BaseBankScraper
from .bte_inspects import BTE_INSPECTS
from .bte_inspects import common
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class BTEScraper(BaseBankScraper):
    """BTE (Banque de Tunisie et des Emirats) credit simulator scraper.

    Simulator URL:
      - https://www.bte.com.tn/fr/nos-simulateurs/simulateur-de-credit

    The simulator is an amortization schedule calculator (amount, rate, periodicity, duration).
    It does not have a built-in eligibility decision; we still return a compatible payload.

    Interface matches the other scrapers:
      navigate() -> fill_form() -> submit_and_wait() -> extract_result()
    """

    def __init__(self, headless: bool = True):
        super().__init__(headless)
        self.inspect = BTE_INSPECTS["SIMULATEUR_CREDIT"]
        self.base_url = self.inspect.URL
        self.current_profile: Optional[Dict[str, Any]] = None

    def run(self, playwright, profile: Dict[str, Any]) -> Dict[str, Any]:
        # single simulator for now
        profile["bte_simulator"] = self.inspect.KEY
        self.base_url = self.inspect.URL
        return super().run(playwright, profile)

    def navigate(self):
        logger.info(f"Navigating BTE {self.inspect.KEY}: {self.base_url}")
        self.page.goto(self.base_url, wait_until="networkidle", timeout=60000)

    def fill_form(self, profile: Dict[str, Any]):
        self.current_profile = profile
        logger.info(f"Filling BTE {self.inspect.KEY} ...")
        self.inspect.fill(self.page, profile)

    def submit_and_wait(self):
        logger.info(f"Submitting BTE {self.inspect.KEY} ...")
        self.inspect.submit_and_wait(self.page)

    def extract_result(self) -> Dict[str, Any]:
        logger.info(f"Extracting BTE {self.inspect.KEY} ...")

        result: Dict[str, Any] = {
            "bank_name": "BTE",
            "result_status": "ERROR",
            "monthly_payment": None,
            "interest_rate": 0.0,
            "details": "",
        }

        schedule, totals = common.extract_schedule_and_totals(self.page)

        monthly = common.pick_regular_payment(schedule)
        result["monthly_payment"] = monthly

        # interest rate is an input on the form; we keep it as-is
        taux = None
        try:
            taux = common.get_input_value_float(self.page, "#taux")
        except Exception:
            taux = None

        if taux is None and self.current_profile:
            taux = common.choose_interest_rate_percent(self.current_profile)

        if taux is not None:
            result["interest_rate"] = float(taux)

        # no eligibility logic on this simulator; treat as "ELIGIBLE" if we got a payment
        if monthly is not None:
            result["result_status"] = "ELIGIBLE"
        else:
            result["result_status"] = "REFUSED"

        # keep a compact details payload (avoid storing the whole schedule)
        details_parts = []
        if totals:
            if totals.get("total_principal") is not None:
                details_parts.append(f"Total principal: {totals['total_principal']}")
            if totals.get("total_interest") is not None:
                details_parts.append(f"Total interets: {totals['total_interest']}")
            if totals.get("total_payment") is not None:
                details_parts.append(f"Total echeances: {totals['total_payment']}")

        if schedule:
            # store first 2 lines for debugging
            preview = schedule[:2]
            details_parts.append(f"Preview: {preview}")

        result["details"] = " | ".join(details_parts)

        # store some debug fields back to profile
        if self.current_profile is not None:
            self.current_profile["bte_res_monthly"] = monthly
            self.current_profile["bte_res_rate"] = result.get("interest_rate")
            if totals:
                self.current_profile["bte_total_interest"] = totals.get("total_interest")
                self.current_profile["bte_total_payment"] = totals.get("total_payment")

        return result
