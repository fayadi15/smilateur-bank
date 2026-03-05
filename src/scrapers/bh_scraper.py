from typing import Dict, Any, Optional

from .base_scraper import BaseBankScraper
from .bh_inspects import BH_INSPECTS
from .bh_inspects import common
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class BhScraper(BaseBankScraper):
    """BH Bank (bhbank.tn) credit simulators scraper.

    Supported simulators:
      - CREDIT_AMENAGEMENT
      - CREDIT_CONSO
      - CREDIT_HABITAT
      - CREDIT_VOITURE

    The scraper follows the same interface used by the other bank scrapers:
      navigate() -> fill_form() -> submit_and_wait() -> extract_result()
    """

    def __init__(self, headless: bool = True):
        super().__init__(headless)
        self.inspect = BH_INSPECTS["CREDIT_CONSO"]
        self.base_url = self.inspect.URL
        self.current_profile: Optional[Dict[str, Any]] = None

    def _pick_inspect(self, profile: Dict[str, Any]):
        # explicit override
        if profile.get("bh_simulator") in BH_INSPECTS:
            return BH_INSPECTS[profile["bh_simulator"]]

        loan_type = (profile.get("loan_type") or "").upper()
        if loan_type == "AUTO":
            return BH_INSPECTS["CREDIT_VOITURE"]
        if loan_type == "IMMO":
            return BH_INSPECTS["CREDIT_HABITAT"]
        if loan_type == "CONSO":
            return BH_INSPECTS["CREDIT_CONSO"]
        # fallback: use aménagement for "other" profiles
        return BH_INSPECTS["CREDIT_AMENAGEMENT"]

    def run(self, playwright, profile: Dict[str, Any]) -> Dict[str, Any]:
        self.inspect = self._pick_inspect(profile)
        self.base_url = self.inspect.URL
        profile["bh_simulator"] = self.inspect.KEY
        return super().run(playwright, profile)

    def navigate(self):
        logger.info(f"Navigating BH {self.inspect.KEY}: {self.base_url}")
        self.page.goto(self.base_url, wait_until="networkidle", timeout=60000)

    def fill_form(self, profile: Dict[str, Any]):
        self.current_profile = profile
        logger.info(f"Filling BH {self.inspect.KEY} ...")
        self.inspect.fill(self.page, profile)

    def submit_and_wait(self):
        logger.info(f"Submitting BH {self.inspect.KEY} ...")
        self.inspect.submit_and_wait(self.page)

    def extract_result(self) -> Dict[str, Any]:
        logger.info(f"Extracting BH {self.inspect.KEY} ...")

        result: Dict[str, Any] = {
            "bank_name": "BH",
            "result_status": "ERROR",
            "monthly_payment": None,
            "interest_rate": 0.0,
            "details": "",
        }

        kv = common.extract_kv(self.page)
        full_text = common.extract_full_text(self.page)
        msg_norm = common.norm_text(full_text or kv.get("__details_text", ""))

        # ---- core fields ----
        monthly = (
            common.safe_float(kv, "Mensualite", "Mensualite du credit")
            or common.safe_float(kv, "Echeance mensuelle cumulee")
            or common.safe_float(kv, "Echeance mensuelle credit direct")
        )
        taux = (
            common.safe_float(kv, "Taux d'interet")
            or common.safe_float(kv, "Taux de credit direct")
        )

        result["monthly_payment"] = monthly
        if taux is not None:
            result["interest_rate"] = float(taux)

        # ---- eligibility rules ----
        refused_by_text = any(
            needle in msg_norm
            for needle in [
                "ne peut pas etre satisfait",
                "ne vous permet pas",
                "il vous manque",
                "non couvert",
            ]
        )

        # requested / authorized amounts
        montant_demande = common.safe_float(kv, "Montant demande")
        montant_autorise = common.safe_float(kv, "Montant autorise", "Credit autorise")

        cout_projet = common.safe_float(kv, "Cout du projet")
        total_credits = common.safe_float(kv, "Total credits", "Credit direct")
        total_apports = common.safe_float(kv, "Total apports propres", "Autofinancement")
        reste_a_fournir = common.safe_float(kv, "Reste a fournir")

        status = "ELIGIBLE"
        if refused_by_text:
            status = "REFUSED"
        else:
            # habitat: use reste_a_fournir if present
            if reste_a_fournir is not None:
                status = "REFUSED" if reste_a_fournir > 0.01 else "ELIGIBLE"
            elif cout_projet is not None and total_credits is not None and total_apports is not None:
                status = "ELIGIBLE" if (total_credits + total_apports + 1e-6) >= cout_projet else "REFUSED"
            elif montant_demande is not None and montant_autorise is not None:
                status = "ELIGIBLE" if (montant_autorise + 1e-6) >= montant_demande else "REFUSED"
            else:
                # fallback: if we got a monthly payment and no refusal message, assume eligible
                status = "ELIGIBLE" if (monthly is not None) else "REFUSED"

        result["result_status"] = status
        result["details"] = full_text or kv.get("__details_text", "") or ""

        # ---- fallback implicit rate if simulator didn't return a taux ----
        if (result.get("interest_rate") or 0.0) <= 0.0 and self.current_profile and monthly:
            try:
                P, n = self.inspect.principal_and_months(self.current_profile)
                if P and n:
                    result["interest_rate"] = common.estimate_annual_rate_percent(float(P), int(n), float(monthly))
            except Exception:
                pass

        # ---- store a couple of extracted values back to profile (debug/analytics) ----
        if self.current_profile is not None:
            self.current_profile["bh_res_monthly"] = monthly
            self.current_profile["bh_res_rate"] = result.get("interest_rate")
            if montant_autorise is not None:
                self.current_profile["bh_res_montant_autorise"] = montant_autorise
            if reste_a_fournir is not None:
                self.current_profile["bh_res_reste_a_fournir"] = reste_a_fournir

        return result
