from playwright.sync_api import sync_playwright
import time

def test_attijari_calc_refined():
    url = "https://www.attijaribank.com.tn/fr/simulateur/crdit-personnel"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle")
        
        # Handle cookies
        try:
            page.click("button:has-text('Accepter')", timeout=2000)
        except:
            pass
            
        print("Filling form...")
        # Use evaluate to force values if needed, but fill should work if we wait
        page.wait_for_selector("#montant_financement")
        page.fill("#montant_financement", "5000")
        page.fill("#duree", "12")
        page.fill("#revenu_mensuel_avant_impot", "1200")
        page.fill("#age", "25")
        
        print("Clicking 'Calculer'...")
        page.click("#calcul_simulateur")
        
        # Wait for #box-recap to be visible or have content
        time.sleep(3)
        
        recap = page.evaluate("""() => {
            const el = document.querySelector('#box-recap');
            return el ? el.innerText : 'NOT FOUND';
        }""")
        print("\n--- RECAP ---")
        print(recap)
        
        browser.close()

if __name__ == "__main__":
    test_attijari_calc_refined()
