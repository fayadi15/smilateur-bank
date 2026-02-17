from playwright.sync_api import sync_playwright
import time

def inspect_attijari_deep():
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
            
        print("Selecting 'Crédit à la consommation'...")
        page.select_option("select#type_credit", "1")
        time.sleep(1)
        
        print("Selecting 'Crédit Voiture neuve'...")
        page.select_option("select#type_financement", "crdit-voiture-neuve")
        time.sleep(2)
        
        # Now look for inputs
        print("\n--- INPUTS AFTER SELECTION ---")
        inputs = page.evaluate("""() => {
            const results = [];
            document.querySelectorAll('input, select, button, label').forEach(el => {
                if(el.offsetParent !== null) { // Only visible elements
                    results.push({
                        tag: el.tagName,
                        id: el.id,
                        name: el.name,
                        type: el.type,
                        placeholder: el.placeholder,
                        text: el.innerText
                    });
                }
            });
            return results;
        }""")
        for s in inputs:
            print(s)
            
        page.screenshot(path="data/attijari_after_selection.png")
        browser.close()

if __name__ == "__main__":
    inspect_attijari_deep()
