from playwright.sync_api import sync_playwright
import time

def inspect_attijari():
    url = "https://www.attijaribank.com.tn/fr/simulateur"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        print(f"Navigating to {url}...")
        page.goto(url, wait_until="networkidle")
        time.sleep(5) # Extra wait for JS
        
        # Take a screenshot
        page.screenshot(path="data/attijari_inspect.png")
        print("Screenshot saved to data/attijari_inspect.png")
        
        # Dump DOM
        with open("data/attijari_inspect.html", "w", encoding="utf-8") as f:
            f.write(page.content())
        print("DOM dumped to data/attijari_inspect.html")
        
        # List selectors
        print("\n--- SELECTORS ---")
        selectors = page.evaluate("""() => {
            const results = [];
            document.querySelectorAll('input, select, button, label').forEach(el => {
                results.push({
                    tag: el.tagName,
                    id: el.id,
                    name: el.name,
                    text: el.innerText || el.value,
                    for: el.getAttribute('for')
                });
            });
            return results;
        }""")
        for s in selectors:
            print(s)
            
        browser.close()

if __name__ == "__main__":
    inspect_attijari()
