from . import common

KEY = "AWAL_SAKAN"
URL = "https://www.biat.tn/biat/Fr/awal-sakan_89_400"


def fill(page, profile: dict):
    amount_dt = int(float(profile.get("montant_pret_demande", 30000)))
    months = int(profile.get("duree_mois", 180))

    project_value = max(int(round(amount_dt / 0.8)), 10000)
    profile["biat_project_value_dt_used"] = project_value
    common.fill_text(page, 'input[name="valeur_projet_immo"]', str(project_value))

    # montant_max auto
    common.wait_non_empty_value(page, 'input[name="montant_max"]', 20000)
    max_dt = common.parse_int(common.get_input_value(page, 'input[name="montant_max"]')) or amount_dt

    used_amount_dt = min(amount_dt, max_dt)
    profile["biat_amount_dt_used"] = used_amount_dt
    common.fill_text(page, 'input[name="amount1"]', str(used_amount_dt))

    years = max(1, int(round(months / 12)))
    y_min, y_max, _ = common.get_slider_range(page, "#slider2", (1, 25, 1))
    used_y = common.clamp(years, y_min, y_max)

    profile["biat_duration_years_used"] = used_y
    profile["biat_duration_mois_used"] = used_y * 12

    common.set_slider_and_input(page, "#slider2", "#amount2", used_y)


def submit_and_wait(page):
    # AWAL SAKAN affiche souvent le résultat sans bouton (ou recalcul automatique)
    common.wait_monthly_result(page, "#remb_mensuel", 25000)


def principal_and_months(profile: dict):
    P = int(profile.get("biat_amount_dt_used", 0))
    n = int(profile.get("biat_duration_mois_used", 0))
    return P, n


def extra_details(page) -> str:
    return ""