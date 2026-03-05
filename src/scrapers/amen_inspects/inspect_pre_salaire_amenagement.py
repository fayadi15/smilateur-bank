from typing import Dict, Any
from . import common


class InspectPreSalaireAmenagement:
    KEY = "PRESALAIRE_AMENAGEMENT"
    URL = common.AMEN_PRE_SALAIRE_URL

    # product values: 1=Préslaire Plus, 2=Crédit Aménagement
    DEFAULT_PRODUCT = "1"

    @staticmethod
    def choose_product(profile: Dict[str, Any]) -> str:
        v = profile.get("amen_product")
        if v is not None:
            try:
                iv = int(v)
                if iv in (1, 2):
                    return str(iv)
            except Exception:
                pass
        # try to map by loan_type
        lt = (profile.get("loan_type") or "").upper()
        if lt in ("AMENAGEMENT", "RENOVATION"):
            return "2"
        return InspectPreSalaireAmenagement.DEFAULT_PRODUCT

    @staticmethod
    def fill(page, profile: Dict[str, Any]):
        page.wait_for_selector("form#SimulatorForm", state="attached", timeout=60000)

        common.select_option(page, "#product", InspectPreSalaireAmenagement.choose_product(profile))
        common.fill_number(page, "#amount", common.choose_amount(profile))

        years = common.choose_duration_years(profile)
        common.fill_number(page, "#drefund", years)

        period = common.choose_periodicity_value(profile)
        common.select_option(page, "#prefund", period)

        # refund select is disabled on UI; leave as default

    @staticmethod
    def submit_and_wait(page):
        common.click_calculate(page)
        common.wait_results(page)
