from typing import Dict, Any
from . import common


class InspectCredimWatani:
    KEY = "CREDIM_WATANI"
    URL = common.AMEN_CREDIM_URL

    # product values:
    # 4=Credim Watani, 5=Credim, 6=Credim Express
    DEFAULT_PRODUCT = "5"

    @staticmethod
    def choose_product(profile: Dict[str, Any]) -> str:
        v = profile.get("amen_product")
        if v is not None:
            try:
                iv = int(v)
                if iv in (4, 5, 6):
                    return str(iv)
            except Exception:
                pass
        # map: IMMO -> Credim (5); fast / conso -> Express (6)
        lt = (profile.get("loan_type") or "").upper()
        if lt in ("IMMO", "IMMOBILIER", "HABITAT"):
            return "5"
        return InspectCredimWatani.DEFAULT_PRODUCT

    @staticmethod
    def fill(page, profile: Dict[str, Any]):
        page.wait_for_selector("form#SimulatorForm", state="attached", timeout=60000)

        common.select_option(page, "#product", InspectCredimWatani.choose_product(profile))
        common.fill_number(page, "#amount", common.choose_amount(profile))

        years = common.choose_duration_years(profile)
        common.fill_number(page, "#drefund", years)

        period = common.choose_periodicity_value(profile)
        common.select_option(page, "#prefund", period)

    @staticmethod
    def submit_and_wait(page):
        common.click_calculate(page)
        common.wait_results(page)
