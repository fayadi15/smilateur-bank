from playwright.sync_api import sync_playwright
import time

def inspect_attijari_form():
    url = "https://www.attijaribank.com.tn/fr/simulateur/crdit-personnel"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle")
        time.sleep(2)
        
        # Handle cookies
        try:
            page.click("button:has-text('Accepter')", timeout=2000)
        except:
            pass
            
        print("Dumping all visible inputs and their labels...")
        inputs = page.evaluate("""() => {
            const results = [];
            document.querySelectorAll('input, select, textarea').forEach(el => {
                const style = window.getComputedStyle(el);
                if (style.display !== 'none' && style.visibility !== 'hidden' && el.type !== 'hidden') {
                    // Try to find label
                    let labelText = '';
                    if (el.id) {
                        const label = document.querySelector(`label[for="${el.id}"]`);
                        if (label) labelText = label.innerText;
                    }
                    if (!labelText) {
                        // Try parent label or sibling
                        let parent = el.parentElement;
                        while(parent && parent.tagName !== 'BODY') {
                            const label = parent.querySelector('label');
                            if (label) {
                                labelText = label.innerText;
                                break;
                            }
                            parent = parent.parentElement;
                        }
                    }
                    results.push({
                        tag: el.tagName,
                        id: el.id,
                        name: el.name,
                        type: el.type,
                        label: labelText,
                        placeholder: el.placeholder
                    });
                }
            });
            return results;
        }""")
        for s in inputs:
            print(s)
            
        browser.close()

if __name__ == "__main__":
    inspect_attijari_form()
