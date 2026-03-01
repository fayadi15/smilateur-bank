from playwright.sync_api import sync_playwright

from src.scrapers.biat_inspects import BIAT_INSPECTS
from src.scrapers.biat_inspects import common


def make_profile(sim_key: str) -> dict:
    """
    Profils de test simples, adaptés aux champs BIAT (en se basant sur tes plages).
    Tu peux ajuster facilement ces valeurs.
    """
    base = {
        "id": f"test-{sim_key}",
        "loan_type": "CONSO",
        "montant_pret_demande": 20000,  # DT
        "duree_mois": 24,               # mois
    }

    if sim_key == "CREDIMEDIA":
        base.update({"montant_pret_demande": 24000, "duree_mois": 24})
    elif sim_key == "CREDIFOYER":
        base.update({"montant_pret_demande": 20000, "duree_mois": 36})
    elif sim_key == "CREDIRENOV":
        base.update({"montant_pret_demande": 30000, "duree_mois": 36})
    elif sim_key == "CREDIAUTO":
        base.update({"loan_type": "AUTO", "montant_pret_demande": 15000, "duree_mois": 48})
    elif sim_key == "BIATIMMO":
        base.update({"loan_type": "IMMO", "montant_pret_demande": 80000, "duree_mois": 180})
    elif sim_key == "FLEXIMMO":
        base.update({"loan_type": "IMMO", "montant_pret_demande": 80000, "duree_mois": 180})
    elif sim_key == "AWAL_SAKAN":
        base.update({"loan_type": "IMMO", "montant_pret_demande": 60000, "duree_mois": 240})
    elif sim_key == "CREDIRESIDENCE":
        base.update({"loan_type": "IMMO", "montant_pret_demande": 30000, "duree_mois": 180})

    return base


def run_one(page, sim_key: str):
    inspect = BIAT_INSPECTS[sim_key]
    profile = make_profile(sim_key)
    profile["biat_simulator"] = sim_key

    page.goto(inspect.URL, wait_until="networkidle", timeout=60000)

    # Fill + submit
    inspect.fill(page, profile)
    inspect.submit_and_wait(page)

    # Extract mensualité
    txt = (page.text_content("#remb_mensuel") or "").strip()
    monthly = common.parse_monthly_payment(txt)

    # details (ex: crediresidence remb_mensuel2)
    details = ""
    try:
        details = inspect.extra_details(page) or ""
    except Exception:
        pass

    # taux implicite
    interest = 0.0
    if monthly:
        P, n = inspect.principal_and_months(profile)
        if P and n:
            interest = common.estimate_annual_rate_percent(float(P), int(n), float(monthly))

    return {
        "sim": sim_key,
        "monthly_payment": monthly,
        "interest_rate": interest,
        "details": details,
        "profile_used": {
            k: v for k, v in profile.items()
            if k.startswith("biat_") or k in ("montant_pret_demande", "duree_mois", "loan_type")
        }
    }


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # mets True si tu veux headless
        page = browser.new_page(locale="fr-FR")

        results = []
        for sim_key in BIAT_INSPECTS.keys():
            print(f"\n===== TEST {sim_key} =====")
            try:
                r = run_one(page, sim_key)
                results.append(r)
                print("Mensualité:", r["monthly_payment"])
                print("Taux estimé:", r["interest_rate"])
                if r["details"]:
                    print("Details:", r["details"])
                print("Profile used:", r["profile_used"])
            except Exception as e:
                print("❌ ERROR:", sim_key, "->", e)

        browser.close()

        print("\n===== SUMMARY =====")
        for r in results:
            print(f"{r['sim']}: mensualité={r['monthly_payment']} | taux={r['interest_rate']} | details={r['details'][:80]}")

if __name__ == "__main__":
    main()