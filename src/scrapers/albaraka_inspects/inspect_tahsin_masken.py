from dataclasses import dataclass
from typing import Dict, Any, Tuple

from . import common


@dataclass(frozen=True)
class Inspect:
    KEY: str
    URL: str
    TYPE_SLUG: str

    def fill(self, page, profile: Dict[str, Any]):
        common.maybe_select_financement(page, self.TYPE_SLUG)

        montant = profile.get("montant_pret_demande")
        if montant is None:
            montant = profile.get("amount")
        if montant is None:
            montant = 20000

        maxv = common.get_input_max(page, "#montant_financement")
        if maxv is not None:
            montant = min(float(montant), float(maxv))

        apport = (
            profile.get("apport_propre")
            or profile.get("autofinancement")
            or profile.get("apport_personnel")
        )
        if apport is None:
            apport = round(float(montant) * 0.1, 3)

        revenu = profile.get("salaire_net") or profile.get("revenu_mensuel") or profile.get("income")
        if revenu is None:
            revenu = 1200

        autres = profile.get("autres_credits") or profile.get("mensualite_autre_financement") or 0

        duree_mois = int(profile.get("duree_mois") or 60)
        duree_ans = max(1, (duree_mois + 11) // 12)

        profile["albaraka_financement_slug"] = self.TYPE_SLUG
        profile["albaraka_input_montant"] = float(montant)
        profile["albaraka_input_apport"] = float(apport)
        profile["albaraka_input_revenu"] = float(revenu)
        profile["albaraka_input_autres"] = float(autres)
        profile["albaraka_input_duree_ans"] = int(duree_ans)

        common.fill_number(page, "#montant_financement", montant)
        common.fill_number(page, "#apport_propre", apport)
        common.fill_number(page, "#revenu_mensuel_avant_impot", revenu)
        chosen = common.select_best_numeric_option(page, "#duree", int(duree_ans))
        profile["albaraka_input_duree_ans_used"] = chosen
        common.fill_number(page, "#mensualite_autre_financement", autres)

    def submit_and_wait(self, page):
        common.click_calculate(page)
        common.wait_box_recap(page)

    def principal_and_months(self, profile: Dict[str, Any]) -> Tuple[float, int]:
        P = float(profile.get("albaraka_input_montant") or profile.get("montant_pret_demande") or 0)
        n = int(profile.get("duree_mois") or 0)
        return P, n


TAHSIN_MASKEN = Inspect(
    KEY="TAHSIN_MASKEN",
    URL="https://www.albaraka.com.tn/fr/simulateur/tahsin-masken-al-baraka",
    TYPE_SLUG="tahsin-masken-al-baraka",
)
