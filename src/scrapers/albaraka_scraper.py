from typing import Dict, Any, Optional

from .base_scraper import BaseBankScraper
from .albaraka_inspects import ALBARAKA_INSPECTS
from .albaraka_inspects import common
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class AlBarakaScraper(BaseBankScraper):
    """Al Baraka Bank simulators scraper.

    Supported simulators (URLs are fixed and each page preselects one product):
      - Dar Al Baraka: https://www.albaraka.com.tn/fr/simulateur/dar-al-baraka
      - Sayarat Al Baraka Neuve 5-8CH: https://www.albaraka.com.tn/fr/simulateur/sayarat-al-baraka-neuve-5-8ch
      - Tahsin Masken: https://www.albaraka.com.tn/fr/simulateur/tahsin-masken-al-baraka
      - Rahalet: https://www.albaraka.com.tn/fr/simulateur/rahalet-al-baraka

    The result card is #box-recap and contains monthly payment, duration, fee and CMR status.
    """

    def __init__(self, headless: bool = True):
        super().__init__(headless)
        self.inspect = ALBARAKA_INSPECTS["DAR_AL_BARAKA"]
        self.base_url = self.inspect.URL
        self.current_profile: Optional[Dict[str, Any]] = None

    def _pick_inspect(self, profile: Dict[str, Any]):
        # explicit override
        if profile.get("albaraka_simulator") in ALBARAKA_INSPECTS:
            return ALBARAKA_INSPECTS[profile["albaraka_simulator"]]

        loan_type = (profile.get("loan_type") or "").upper()
        if loan_type == "AUTO":
            return ALBARAKA_INSPECTS["SAYARAT_NEUVE_5_8CH"]
        if loan_type in ("IMMO", "HABITAT", "IMMOBILIER"):
            return ALBARAKA_INSPECTS["DAR_AL_BARAKA"]
        if loan_type in ("AMENAGEMENT", "RENOVATION"):
            return ALBARAKA_INSPECTS["TAHSIN_MASKEN"]
        if loan_type in ("VOYAGE", "OMRA", "TRAVEL"):
            return ALBARAKA_INSPECTS["RAHALET"]
        return ALBARAKA_INSPECTS["DAR_AL_BARAKA"]

    def run(self, playwright, profile: Dict[str, Any]) -> Dict[str, Any]:
        self.inspect = self._pick_inspect(profile)
        self.base_url = self.inspect.URL
        profile["albaraka_simulator"] = self.inspect.KEY
        return super().run(playwright, profile)

    def navigate(self):
        logger.info(f"Navigating ALBARAKA {self.inspect.KEY}: {self.base_url}")
        self.page.goto(self.base_url, wait_until="networkidle", timeout=60000)

    def fill_form(self, profile: Dict[str, Any]):
        self.current_profile = profile
        logger.info(f"Filling ALBARAKA {self.inspect.KEY} ...")
        self.inspect.fill(self.page, profile)

    def submit_and_wait(self):
        logger.info(f"Submitting ALBARAKA {self.inspect.KEY} ...")
        self.inspect.submit_and_wait(self.page)

    def extract_result(self) -> Dict[str, Any]:
        logger.info(f"Extracting ALBARAKA {self.inspect.KEY} ...")

        result: Dict[str, Any] = {
            "bank_name": "ALBARAKA",
            "result_status": "ERROR",
            "monthly_payment": None,
            "interest_rate": 0.0,
            "details": "",
        }

        recap = common.extract_recap(self.page)

        result["monthly_payment"] = recap.monthly_payment

        # Determine eligibility
        if recap.cmr_ok is True:
            result["result_status"] = "ELIGIBLE"
        elif recap.cmr_ok is False:
            result["result_status"] = "REFUSED"
        else:
            # fallback: check raw label
            txt = common.norm_text(recap.raw_text)
            if "cmr suffisante" in txt:
                result["result_status"] = "ELIGIBLE"
            elif "cmr insuffisante" in txt:
                result["result_status"] = "REFUSED"
            else:
                result["result_status"] = "REFUSED" if recap.monthly_payment is None else "ELIGIBLE"

        # details
        parts = []
        if recap.cmr_percent is not None:
            parts.append(f"CMR: {recap.cmr_percent:.2f}%")
        if recap.fees is not None:
            parts.append(f"Frais dossier: {recap.fees}")
        if recap.duration_months is not None:
            parts.append(f"Duree: {recap.duration_months} mois")
        if recap.requested_amount is not None:
            parts.append(f"Montant: {recap.requested_amount}")
        result["details"] = " | ".join(parts) if parts else recap.raw_text

        # store debug fields back into profile
        if self.current_profile is not None:
            self.current_profile["albaraka_res_monthly"] = recap.monthly_payment
            self.current_profile["albaraka_res_cmr_percent"] = recap.cmr_percent
            self.current_profile["albaraka_res_fees"] = recap.fees
            self.current_profile["albaraka_res_duration_months"] = recap.duration_months
            self.current_profile["albaraka_res_requested_amount"] = recap.requested_amount
            self.current_profile["albaraka_res_status"] = result["result_status"]

        return result
