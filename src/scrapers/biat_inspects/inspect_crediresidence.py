from . import common

KEY = "CREDIRESIDENCE"
URL = "https://www.biat.tn/biat/Fr/crediresidence_83_336"


def fill(page, profile: dict):
    amount_dt = int(float(profile.get("montant_pret_demande", 15000)))
    months = int(profile.get("duree_mois", 120))

    profile["biat_amount_dt_used"] = amount_dt
    common.fill_text(page, 'input[name="amount1"]', str(amount_dt))

    years = max(1, int(round(months / 12)))
    y_min, y_max, _ = common.get_slider_range(page, "#slider2", (1, 25, 1))
    used_y = common.clamp(years, y_min, y_max)

    profile["biat_duration_years_used"] = used_y
    profile["biat_duration_mois_used"] = used_y * 12

    common.set_slider_and_input(page, "#slider2", "#amount2", used_y)


def submit_and_wait(page):
    # pas de bouton dans ton HTML -> recalcul automatique
    common.wait_monthly_result(page, "#remb_mensuel", 25000)


def principal_and_months(profile: dict):
    P = int(profile.get("biat_amount_dt_used", 0))
    n = int(profile.get("biat_duration_mois_used", 0))
    return P, n


def extra_details(page) -> str:
    # il y a un message conditionnel dans #remb_mensuel2
    try:
        if page.is_visible("#remb_mensuel2"):
            return (page.text_content("#remb_mensuel2") or "").strip()
    except Exception:
        pass
    return ""