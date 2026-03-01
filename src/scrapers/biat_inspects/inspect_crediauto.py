from . import common

KEY = "CREDIAUTO"
URL = "https://www.biat.tn/biat/Fr/crediauto_79_332"


def fill(page, profile: dict):
    # Valeur véhicule (pas dans profile generator) -> défaut basé sur montant demandé
    amount_dt = int(float(profile.get("montant_pret_demande", 15000)))
    vehicle_value = max(int(round(amount_dt * 1.67)), 5000)  # ~60% financé
    profile["biat_vehicle_value_dt_used"] = vehicle_value

    common.fill_text(page, 'input[name="valeur_vehicule"]', str(vehicle_value))

    # Puissance fiscale (défaut: 5-8CV = value "58")
    pf = str(profile.get("biat_puissance_fiscale", "58"))
    profile["biat_puissance_fiscale_used"] = pf
    common.check_radio(page, f'input[name="puissance_fiscale"][value="{pf}"]')

    # attendre calcul montant_max
    common.wait_non_empty_value(page, 'input[name="montant_max"]', 20000)
    montant_max_txt = common.get_input_value(page, 'input[name="montant_max"]')
    montant_max_dt = common.parse_int(montant_max_txt) or amount_dt

    credit_amount_dt = min(amount_dt, montant_max_dt)
    profile["biat_credit_amount_dt_used"] = credit_amount_dt

    # Slider montant (#slider1) + input (#amount1) (même si parfois caché)
    try:
        common.set_slider_and_input(page, "#slider1", "#amount1", credit_amount_dt)
    except Exception:
        # fallback: set input only
        page.evaluate(
            """(val)=>{
                const el=document.querySelector('#amount1');
                if(el){ el.value=String(val); el.dispatchEvent(new Event('change',{bubbles:true})); }
            }""",
            credit_amount_dt,
        )

    # Durée (mois) slider2 (max 84)
    months = int(profile.get("duree_mois", 24))
    d_min, d_max, _ = common.get_slider_range(page, "#slider2", (3, 84, 1))
    used_m = common.clamp(months, d_min, d_max)
    profile["biat_duration_mois_used"] = used_m

    common.set_slider_and_input(page, "#slider2", "#amount2", used_m)


def submit_and_wait(page):
    page.wait_for_selector("input#bt_crediauto_simulateur", state="visible", timeout=20000)
    try:
        with page.expect_navigation(wait_until="networkidle", timeout=15000):
            page.click("input#bt_crediauto_simulateur")
    except Exception:
        page.click("input#bt_crediauto_simulateur")

    common.wait_monthly_result(page, "#remb_mensuel", 25000)


def principal_and_months(profile: dict):
    P = int(profile.get("biat_credit_amount_dt_used", 0))
    n = int(profile.get("biat_duration_mois_used", 0))
    return P, n


def extra_details(page) -> str:
    return ""