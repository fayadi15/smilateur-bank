import requests
from bs4 import BeautifulSoup

url = "https://www.banquezitouna.com/fr/particuliers/simulateur"
try:
    response = requests.get(url, timeout=15)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    print("--- SUBMIT CANDIDATES ---")
    # Inputs with type submit
    submits = soup.find_all('input', type='submit')
    for s in submits:
        print(f"INPUT SUBMIT: id='{s.get('id')}' name='{s.get('name')}' value='{s.get('value')}' class='{s.get('class')}'")

    # Buttons
    buttons = soup.find_all('button')
    for b in buttons:
        print(f"BUTTON: id='{b.get('id')}' text='{b.text.strip()}' class='{b.get('class')}'")

    # Links acting as buttons
    links = soup.find_all('a')
    for l in links:
        if 'simul' in l.text.lower():
            print(f"LINK: text='{l.text.strip()}' href='{l.get('href')}' class='{l.get('class')}' id='{l.get('id')}'")
            
except Exception as e:
    print(f"Error: {e}")
