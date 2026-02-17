import requests
from bs4 import BeautifulSoup

url = "https://www.banquezitouna.com/fr/particuliers/simulateur"
try:
    response = requests.get(url, timeout=15)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    print("--- POTENTIAL FINANCIAL INPUTS ---")
    # Find all inputs
    inputs = soup.find_all('input')
    for inp in inputs:
        name = inp.get('name', '').lower()
        id_ = inp.get('id', '').lower()
        placeholder = inp.get('placeholder', '').lower()
        cls = " ".join(inp.get('class', [])).lower()
        
        # Filter for relevant keywords
        keywords = ['montant', 'prix', 'duree', 'salaire', 'revenu', 'apport', 'amount', 'duration', 'salary', 'financement']
        if any(k in name or k in id_ or k in placeholder or k in cls for k in keywords):
            print(f"INPUT: id='{inp.get('id')}' name='{inp.get('name')}' placeholder='{inp.get('placeholder')}' type='{inp.get('type')}'")

    print("\n--- POTENTIAL SELECTS ---")
    selects = soup.find_all('select')
    for sel in selects:
        print(f"SELECT: id='{sel.get('id')}' name='{sel.get('name')}'")
        # Print options
        for opt in sel.find_all('option')[:3]:
            print(f"  OPT: val='{opt.get('value')}' text='{opt.text.strip()}'")

    print("\n--- BUTTONS ---")
    buttons = soup.find_all('button')
    for btn in buttons:
         print(f"BUTTON: id='{btn.get('id')}' text='{btn.text.strip()}' class='{btn.get('class')}'")

except Exception as e:
    print(f"Error: {e}")
