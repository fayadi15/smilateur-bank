from . import common

KEY = "CREDIT_AMENAGEMENT"
URL = "https://www.bhbank.tn/cr%C3%A9dit-am%C3%A9nagement"


def fill(page, profile: dict):
    # Inputs
    montant = float(profile.get("montant_pret_demande", 10000) or 10000)
    autres = float(profile.get("autres_credits", 0) or 0)
    age = int(profile.get("age", 35) or 35)
    salaire = float(profile.get("salaire_net", 1500) or 1500)

    duree_ans = common.months_to_years(profile.get("duree_mois", 36), min_years=1, max_years=7)
    categorie = common.categorize_from_profile(profile)

    # Store debug
    profile["bh_simulator"] = KEY
    profile["bh_montant_credit"] = int(round(montant))
    profile["bh_engagement_mensuels"] = float(autres)
    profile["bh_age_client"] = age
    profile["bh_revenu_mensuel"] = float(salaire)
    profile["bh_duree_ans_used"] = duree_ans
    profile["bh_duree_mois_used"] = duree_ans * 12
    profile["bh_categorie_used"] = categorie

    # Fill
    common.fill_text(page, "#montant", int(round(montant)))
    common.fill_text(page, "#engagement_mensuels", float(autres))
    common.select_option(page, "#categorie", categorie)
    common.fill_text(page, "#age_client", age)
    common.select_option(page, "#duree", str(duree_ans))

    # Revenus: monthly by default
    common.check_radio(page, "#mois")
    common.fill_text(page, "#revenue", float(salaire))


def submit_and_wait(page):
    common.click_calculer(page)
    common.wait_result(page)


def principal_and_months(profile: dict):
    P = int(profile.get("bh_montant_credit", 0) or 0)
    n = int(profile.get("bh_duree_mois_used", 0) or 0)
    return max(P, 0), n
