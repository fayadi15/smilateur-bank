from typing import Dict, Any, Optional

from .base_scraper import BaseBankScraper
from .amen_inspects import AMEN_INSPECTS
from .amen_inspects import common
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class AmenScraper(BaseBankScraper):
    """Amen Bank simulators scraper.

    Pages (same HTML structure, different product options):
      - Presalaire / Amenagement: https://www.amenbank.com.tn/fr/simulateur-pre-salaire-amenagement.html
      - Auto Invest:              https://www.amenbank.com.tn/fr/simulateur-auto-invest.html
      - Credim / Watani:          https://www.amenbank.com.tn/fr/simulateur-credim-watani.html

    The simulator returns an "Echéances" value with a chosen periodicity (monthly/quarterly/...).
    We convert it to a monthly equivalent to align with the rest of the project.
    """

    def __init__(self, headless: bool = True):
        super().__init__(headless)
        self.inspect = AMEN_INSPECTS["PRESALAIRE_AMENAGEMENT"]
        self.base_url = self.inspect.URL
        self.current_profile: Optional[Dict[str, Any]] = None

    def _pick_inspect(self, profile: Dict[str, Any]):
        # user override
        key = profile.get("amen_simulator")
        if key in AMEN_INSPECTS:
            return AMEN_INSPECTS[key]

        loan_type = (profile.get("loan_type") or "").upper()
        if loan_type == "AUTO":
            return AMEN_INSPECTS["AUTO_INVEST"]
        if loan_type in ("IMMO", "IMMOBILIER", "HABITAT"):
            return AMEN_INSPECTS["CREDIM_WATANI"]
        # default
        return AMEN_INSPECTS["PRESALAIRE_AMENAGEMENT"]

    def run(self, playwright, profile: Dict[str, Any]) -> Dict[str, Any]:
        self.inspect = self._pick_inspect(profile)
        self.base_url = self.inspect.URL
        profile["amen_simulator"] = self.inspect.KEY
        return super().run(playwright, profile)

    def navigate(self):
        logger.info(f"Navigating AMEN {self.inspect.KEY}: {self.base_url}")
        self.page.goto(self.base_url, wait_until="networkidle", timeout=60000)

    def fill_form(self, profile: Dict[str, Any]):
        self.current_profile = profile
        logger.info(f"Filling AMEN {self.inspect.KEY} ...")
        self.inspect.fill(self.page, profile)

    def submit_and_wait(self):
        logger.info(f"Submitting AMEN {self.inspect.KEY} ...")
        self.inspect.submit_and_wait(self.page)

    def extract_result(self) -> Dict[str, Any]:
        logger.info(f"Extracting AMEN {self.inspect.KEY} ...")

        result: Dict[str, Any] = {
            "bank_name": "AmenBank",
            "result_status": "ERROR",
            "monthly_payment": None,
            "interest_rate": 0.0,
            "details": "",
        }

        # periodicity used
        period_value = "1"
        try:
            # the form selection value reflects months per period (1/3/6/12)
            period_value = self.page.input_value("#prefund")
        except Exception:
            # fallback to profile selection
            if self.current_profile:
                period_value = common.choose_periodicity_value(self.current_profile)

        echeance, monthly, taux, kv = common.get_result_fields(self.page, period_value)

        if monthly is not None:
            result["monthly_payment"] = float(monthly)
            result["result_status"] = "ELIGIBLE"
        else:
            result["result_status"] = "REFUSED"

        if taux is not None:
            result["interest_rate"] = float(taux)

        # compact details
        product_label = common.get_selected_option_text(self.page, "#product") or ""
        details_parts = [
            f"Product: {product_label}",
            f"PeriodMonths: {common.months_per_period(period_value)}",
        ]
        if echeance is not None:
            details_parts.append(f"EcheancePeriode: {echeance}")
        if kv:
            # include key summary
            for k in ("Nbre Echéances", "Durée de remboursement (années)", "Périodicité de remboursement"):
                if k in kv:
                    details_parts.append(f"{k}: {kv[k]}")
        result["details"] = " | ".join(details_parts)

        # store debug fields back to profile
        if self.current_profile is not None:
            self.current_profile["amen_res_echeance"] = echeance
            self.current_profile["amen_res_monthly"] = result.get("monthly_payment")
            self.current_profile["amen_res_rate"] = result.get("interest_rate")
            self.current_profile["amen_product_label"] = product_label

        return result
