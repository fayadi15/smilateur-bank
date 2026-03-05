from . import common

KEY = "CREDIT_HABITAT"
URL = "https://www.bhbank.tn/cr%C3%A9dit-habitat"


def fill(page, profile: dict):
    # In BH habitat simulator, the user inputs project cost + personal contribution.
    desired_credit = float(profile.get("montant_pret_demande", 100000) or 100000)

    if profile.get("bh_project_cost") and profile.get("bh_apport") is not None:
        cost = float(profile["bh_project_cost"])
        apport = float(profile["bh_apport"])
    else:
        cost, apport = common.cost_from_credit_amount(desired_credit, min_apport_ratio=0.2)

    autres = float(profile.get("autres_credits", 0) or 0)
    age = int(profile.get("age", 35) or 35)
    salaire = float(profile.get("salaire_net", 2500) or 2500)

    duree_ans = common.months_to_years(profile.get("duree_mois", 180), min_years=1, max_years=25)
    categorie = common.categorize_from_profile(profile)

    # Store debug
    profile["bh_simulator"] = KEY
    profile["bh_credit_desired"] = int(round(desired_credit))
    profile["bh_project_cost"] = int(round(cost))
    profile["bh_apport"] = int(round(apport))
    profile["bh_engagement_mensuels"] = float(autres)
    profile["bh_age_client"] = age
    profile["bh_revenu_mensuel"] = float(salaire)
    profile["bh_duree_ans_used"] = duree_ans
    profile["bh_duree_mois_used"] = duree_ans * 12
    profile["bh_categorie_used"] = categorie

    # Fill form
    common.fill_text(page, "#montant", int(round(cost)))
    common.fill_text(page, "#autFin", int(round(apport)))
    common.fill_text(page, "#engagement_mensuels", float(autres))
    common.fill_text(page, "#age_client", age)
    duree_ans = common.select_best_numeric_option(page, "#duree", duree_ans)
    profile["bh_duree_ans_used"] = duree_ans
    profile["bh_duree_mois_used"] = duree_ans * 12

    # Revenus
    # monthly is checked by default, but make it explicit
    common.check_radio(page, "#mois")
    common.fill_text(page, "#revenue", float(salaire))

    common.select_option(page, "#categorie", categorie)


def submit_and_wait(page):
    common.click_calculer(page)
    common.wait_result(page)


def principal_and_months(profile: dict):
    # We try to approximate principal as the desired credit amount (cost - apport)
    P = int(profile.get("bh_credit_desired", 0) or 0)
    n = int(profile.get("bh_duree_mois_used", 0) or 0)
    return max(P, 0), n
