from typing import Dict, Any
from . import common


class InspectAutoInvest:
    KEY = "AUTO_INVEST"
    URL = common.AMEN_AUTO_INVEST_URL

    @staticmethod
    def fill(page, profile: Dict[str, Any]):
        page.wait_for_selector("form#SimulatorForm", state="attached", timeout=60000)

        # only option: 3=Auto invest
        common.select_option(page, "#product", "3")
        common.fill_number(page, "#amount", common.choose_amount(profile))

        years = common.choose_duration_years(profile)
        common.fill_number(page, "#drefund", years)

        period = common.choose_periodicity_value(profile)
        common.select_option(page, "#prefund", period)

    @staticmethod
    def submit_and_wait(page):
        common.click_calculate(page)
        common.wait_results(page)
