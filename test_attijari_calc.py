from playwright.sync_api import sync_playwright
import time

def test_attijari_calc():
    url = "https://www.attijaribank.com.tn/fr/simulateur"
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
        page.select_option("select#type_credit", "1")
        time.sleep(1)
        page.select_option("select#type_financement", "crdit-personnel")
        time.sleep(1)
        
        # Fill fields (standard values for test)
        page.fill("#montant_financement", "10000")
        page.fill("#duree", "36")
        page.fill("#revenu_mensuel_avant_impot", "1500")
        page.fill("#age", "30")
        
        print("Clicking 'Calculer'...")
        page.click("#calcul_simulateur")
        time.sleep(3)
        
        # Check for results
        print("\n--- RESULTS SECTION ---")
        # Attijari usually shows a recap box: #box-recap
        results_html = page.evaluate("""() => {
            const el = document.querySelector('#box-recap');
            return el ? el.innerText : 'Not Found';
        }""")
        print(results_html)
        
        page.screenshot(path="data/attijari_result_test.png")
        
        # Dump the result HTML for precise regex
        recap_content = page.evaluate("""() => {
            const el = document.querySelector('#box-recap');
            return el ? el.innerHTML : '';
        }""")
        with open("data/attijari_recap.html", "w", encoding="utf-8") as f:
            f.write(recap_content)
            
        browser.close()

if __name__ == "__main__":
    test_attijari_calc()
