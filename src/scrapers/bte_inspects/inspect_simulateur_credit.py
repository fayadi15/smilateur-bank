from dataclasses import dataclass
from typing import Dict, Any, Tuple

from . import common


@dataclass(frozen=True)
class Inspect:
    KEY: str
    URL: str

    def fill(self, page, profile: Dict[str, Any]):
        # Amount
        montant = profile.get("montant_pret_demande")
        if montant is None:
            montant = profile.get("amount")
        if montant is None:
            montant = 10000

        # Rate
        taux = common.choose_interest_rate_percent(profile)

        # Periodicity: default monthly
        periode = str(profile.get("bte_periode") or "12")

        # Duration as years + months
        duree_mois = profile.get("duree_mois")
        years, months = common.months_to_years_months(int(duree_mois) if duree_mois is not None else 60)

        # Some profiles may have 0y 0m
        if years == 0 and months == 0:
            years = 1

        profile["bte_input_montant"] = int(montant)
        profile["bte_input_taux"] = float(taux)
        profile["bte_input_periode"] = int(periode)
        profile["bte_input_years"] = years
        profile["bte_input_months"] = months

        common.fill_number(page, "#montant", int(montant))
        common.fill_number(page, "#taux", float(taux))
        common.select_option(page, "#Periode", str(periode))
        common.fill_number(page, "#paran", int(years))
        common.fill_number(page, "#parmois", int(months))

    def submit_and_wait(self, page):
        common.click_submit(page)
        common.wait_result_table(page)

    def principal_and_months(self, profile: Dict[str, Any]) -> Tuple[float, int]:
        P = float(profile.get("montant_pret_demande") or 0)
        n = int(profile.get("duree_mois") or 0)
        return P, n


SIMULATEUR_CREDIT = Inspect(
    KEY="SIMULATEUR_CREDIT",
    URL=common.BTE_URL,
)
