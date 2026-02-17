import requests
from bs4 import BeautifulSoup

url = "https://www.banquezitouna.com/fr/particuliers/simulateur"
try:
    response = requests.get(url, timeout=15)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    print("--- LABELS MAP ---")
    labels = soup.find_all('label')
    for lbl in labels:
        for_id = lbl.get('for')
        text = lbl.text.strip().replace('\n', ' ').replace('\r', '')
        if for_id:
            print(f"LABEL: text='{text}' FOR='{for_id}'")
            
except Exception as e:
    print(f"Error: {e}")
