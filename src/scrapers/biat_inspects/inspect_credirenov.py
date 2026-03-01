from . import common

KEY = "CREDIRENOV"
URL = "https://www.biat.tn/biat/Fr/credirenov_80_333"


def fill(page, profile: dict):
    amount_dt = int(float(profile.get("montant_pret_demande", 20000)))
    months = int(profile.get("duree_mois", 24))

    # valeur_traveaux (défaut) pour générer un montant_max suffisant
    valeur_tr = max(int(round(amount_dt / 0.8)), 10000)  # max 80% du projet
    profile["biat_valeur_traveaux_dt_used"] = valeur_tr
    common.fill_text(page, 'input[name="valeur_traveaux"]', str(valeur_tr))

    common.wait_non_empty_value(page, 'input[name="montant_max"]', 20000)
    max_txt = common.get_input_value(page, 'input[name="montant_max"]')
    montant_max_dt = common.parse_int(max_txt) or amount_dt

    # Montant slider1 en mD (max visible 40 mD)
    target_md = int(round(min(amount_dt, montant_max_dt) / 1000))
    a_min, a_max, _ = common.get_slider_range(page, "#slider1", (1, 40, 1))
    used_md = common.clamp(target_md, a_min, a_max)
    profile["biat_amount_md_used"] = used_md

    # Durée slider2 (max 60 mois)
    d_min, d_max, _ = common.get_slider_range(page, "#slider2", (3, 60, 1))
    used_m = common.clamp(months, d_min, d_max)
    profile["biat_duration_mois_used"] = used_m

    common.set_slider_and_input(page, "#slider1", "#amount1", used_md)
    common.set_slider_and_input(page, "#slider2", "#amount2", used_m)


def submit_and_wait(page):
    page.wait_for_selector("input#bt_credirenov_simulateur", state="visible", timeout=20000)
    try:
        with page.expect_navigation(wait_until="networkidle", timeout=15000):
            page.click("input#bt_credirenov_simulateur")
    except Exception:
        page.click("input#bt_credirenov_simulateur")

    common.wait_monthly_result(page, "#remb_mensuel", 25000)


def principal_and_months(profile: dict):
    P = int(profile.get("biat_amount_md_used", 0)) * 1000
    n = int(profile.get("biat_duration_mois_used", 0))
    return P, n


def extra_details(page) -> str:
    return ""