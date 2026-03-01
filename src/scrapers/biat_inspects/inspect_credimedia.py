from . import common

KEY = "CREDIMEDIA"
URL = "https://www.biat.tn/biat/Fr/credimedia_78_331"


def fill(page, profile: dict):
    # montant en DT -> mD
    amount_dt = int(float(profile.get("montant_pret_demande", 10000)))
    target_md = int(round(amount_dt / 1000))

    months = int(profile.get("duree_mois", 12))

    a_min, a_max, _ = common.get_slider_range(page, "#slider1", (1, 30, 1))
    d_min, d_max, _ = common.get_slider_range(page, "#slider2", (3, 36, 1))

    used_md = common.clamp(target_md, a_min, a_max)
    used_m = common.clamp(months, d_min, d_max)

    profile["biat_amount_md_used"] = used_md
    profile["biat_duration_mois_used"] = used_m

    common.set_slider_and_input(page, "#slider1", "#amount1", used_md)
    common.set_slider_and_input(page, "#slider2", "#amount2", used_m)


def submit_and_wait(page):
    page.wait_for_selector("a#bt_credimedia_simulateur", state="visible", timeout=20000)
    page.click("a#bt_credimedia_simulateur")
    common.wait_monthly_result(page, "#remb_mensuel", 20000)


def principal_and_months(profile: dict):
    # principal = mD * 1000 DT
    P = int(profile.get("biat_amount_md_used", 0)) * 1000
    n = int(profile.get("biat_duration_mois_used", 0))
    return P, n


def extra_details(page) -> str:
    return ""