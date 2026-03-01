from playwright.sync_api import sync_playwright

from src.scrapers.biat_inspects import BIAT_INSPECTS
from src.scrapers.biat_inspects import common
from src.database.db_manager import DatabaseManager


def make_profile(sim_key: str) -> dict:
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

    inspect.fill(page, profile)
    inspect.submit_and_wait(page)

    txt = (page.text_content("#remb_mensuel") or "").strip()
    monthly = common.parse_monthly_payment(txt)

    details = ""
    try:
        details = inspect.extra_details(page) or ""
    except Exception:
        pass

    interest = 0.0
    if monthly:
        P, n = inspect.principal_and_months(profile)
        if P and n:
            interest = common.estimate_annual_rate_percent(float(P), int(n), float(monthly))

    return profile, monthly, interest, details


def main():
    db = DatabaseManager()
    db.init_db()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

        # IMPORTANT: créer un context stable une seule fois
        context = browser.new_context(locale="fr-FR")

        for sim_key in BIAT_INSPECTS.keys():
            print(f"\n===== TEST {sim_key} =====")

            # IMPORTANT: une nouvelle page par simulateur
            page = context.new_page()

            try:
                profile, monthly, interest, details = run_one(page, sim_key)

                if details:
                    profile["biat_details"] = details

                status = "ELIGIBLE" if monthly is not None else "ERROR"

                db.insert_result(
                    profile_data=profile,
                    bank_name="BIAT",
                    result_status=status,
                    monthly_payment=monthly,
                    interest_rate=interest,
                )

                print(f"Inserted ✅ {sim_key} | mensualité={monthly} | taux={interest}")

            except Exception as e:
                # Enregistrer l'erreur en DB aussi
                profile = make_profile(sim_key)
                profile["biat_simulator"] = sim_key
                profile["biat_error"] = str(e)

                db.insert_result(
                    profile_data=profile,
                    bank_name="BIAT",
                    result_status="ERROR",
                    monthly_payment=None,
                    interest_rate=None,
                )

                print(f"❌ ERROR: {sim_key} -> {e} (inserted ERROR)")

            finally:
                # Toujours fermer la page (évite l'état cassé)
                try:
                    page.close()
                except Exception:
                    pass

        try:
            context.close()
        except Exception:
            pass
        browser.close()

    db.close()
    print("\nDone.")


if __name__ == "__main__":
    main()