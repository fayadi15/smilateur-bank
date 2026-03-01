from . import common

KEY = "CREDIT_CONSO"
URL = "https://www.stb.com.tn/fr/simulateurs/simulateurs-credit/simulateur-credit-consommations/"

def fill(page, profile: dict):
    typecredit = profile.get("std_typecredit", "PDAA08")
    common.select_option(page, "#TypeCredit", typecredit)

    montant = int(float(profile.get("montant_pret_demande", 10000)))
    salaire = int(float(profile.get("salaire_net", 2000) or 2000))
    autres = int(float(profile.get("autres_credits", 0) or 0))

    duree_mois = int(profile.get("duree_mois", 36))
    duree_ans = max(1, min(3, int(round(duree_mois / 12))))

    profile["std_simulator"] = KEY
    profile["std_typecredit_used"] = typecredit
    profile["std_montant_total"] = montant
    profile["std_salaire_brut"] = salaire
    profile["std_autres_mensualites"] = autres
    profile["std_duree_ans_used"] = duree_ans
    profile["std_duree_mois_used"] = duree_ans * 12

    common.fill_text(page, "#Montant", str(montant))
    common.fill_text(page, "#SalaireBrut", str(salaire))
    common.fill_text(page, "#encoursmensuel", str(autres))
    common.select_option(page, "#Duree", str(duree_ans))

def submit_and_wait(page):
    if common.simulate_via_ajax(page):
        return
    common.click_simuler(page)
    common.wait_result(page)

def principal_and_months(profile: dict):
    P = int(profile.get("std_montant_total", 0))
    n = int(profile.get("std_duree_mois_used", 0))
    return max(P, 0), n

def extra_details(page) -> str:
    _, _, msg, _ = common.get_result_fields(page)
    return msg