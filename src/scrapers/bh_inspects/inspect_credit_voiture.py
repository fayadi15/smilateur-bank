from . import common

KEY = "CREDIT_VOITURE"
URL = "https://www.bhbank.tn/cr%C3%A9dit-voiture"


def fill(page, profile: dict):
    # In BH car simulator, the user inputs vehicle price, and the simulator computes
    # (credit demandé, autofinancement). From observed examples, credit ~= 60% of price.
    desired_credit = float(profile.get("montant_pret_demande", 20000) or 20000)

    credit_ratio = float(profile.get("bh_credit_ratio", 0.6) or 0.6)
    price = float(profile.get("bh_vehicle_price", 0) or 0)
    if price <= 0:
        price = common.price_from_credit_amount(desired_credit, credit_ratio=credit_ratio)

    autres = float(profile.get("autres_credits", 0) or 0)
    age = int(profile.get("age", 40) or 40)
    salaire = float(profile.get("salaire_net", 1850) or 1850)

    duree_ans = common.months_to_years(profile.get("duree_mois", 60), min_years=5, max_years=7)
    categorie = common.categorize_from_profile(profile)

    type_voiture = str(profile.get("bh_type_voiture", "2"))  # default: Neuve > 4 chevaux

    profile["bh_simulator"] = KEY
    profile["bh_credit_desired"] = int(round(desired_credit))
    profile["bh_vehicle_price"] = int(round(price))
    profile["bh_credit_ratio"] = credit_ratio
    profile["bh_engagement_mensuels"] = float(autres)
    profile["bh_age_client"] = age
    profile["bh_revenu_mensuel"] = float(salaire)
    profile["bh_duree_ans_used"] = duree_ans
    profile["bh_duree_mois_used"] = duree_ans * 12
    profile["bh_categorie_used"] = categorie
    profile["bh_type_voiture_used"] = type_voiture

    common.select_option(page, "#type_voiture", type_voiture)
    common.fill_text(page, "#montant", int(round(price)))

    # Wait a moment for autofinancement to update (readonly field)
    page.wait_for_timeout(150)

    common.fill_text(page, "#engagement_mensuels", float(autres))
    common.fill_text(page, "#age_client", age)

    common.check_radio(page, "#mois")
    common.fill_text(page, "#revenue", float(salaire))

    common.select_option(page, "#categorie", categorie)
    common.select_option(page, "#duree", str(duree_ans))


def submit_and_wait(page):
    common.click_calculer(page)
    common.wait_result(page)


def principal_and_months(profile: dict):
    # We try to approximate the loan principal as the requested credit amount.
    # If the simulator uses a different ratio, we'll still have the monthly payment + taux displayed.
    P = int(profile.get("bh_credit_desired", 0) or 0)
    n = int(profile.get("bh_duree_mois_used", 0) or 0)
    return max(P, 0), n
