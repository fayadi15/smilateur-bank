from playwright.sync_api import sync_playwright
import time

def inspect_attijari_slug():
    url = "https://www.attijaribank.com.tn/fr/simulateur/crdit-personnel"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle")
        time.sleep(3)
        
        # Look for inputs
        inputs = page.evaluate("""() => {
            const results = [];
            document.querySelectorAll('input, select, button, label').forEach(el => {
                results.push({
                    tag: el.tagName,
                    id: el.id,
                    name: el.name,
                    label: document.querySelector(`label[for="${el.id}"]`)?.innerText || '',
                    value: el.value
                });
            });
            return results;
        }""")
        for s in inputs:
            print(s)
            
        page.screenshot(path="data/attijari_crdit_personnel.png")
        browser.close()

if __name__ == "__main__":
    inspect_attijari_slug()
