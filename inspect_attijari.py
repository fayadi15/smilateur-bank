import requests
from bs4 import BeautifulSoup

url = "https://www.attijaribank.com.tn/fr/simulateur"
try:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(url, headers=headers, timeout=15)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    print("--- LABELS MAP ---")
    labels = soup.find_all('label')
    for lbl in labels:
        for_id = lbl.get('for')
        text = lbl.text.strip().replace('\n', ' ').replace('\r', '')
        if for_id:
            print(f"LABEL: text='{text}' FOR='{for_id}'")
            
    print("\n--- INPUTS ---")
    inputs = soup.find_all(['input', 'select', 'button'])
    for inp in inputs:
        name = inp.get('name')
        id_ = inp.get('id')
        type_ = inp.get('type')
        print(f"TAG={inp.name} ID={id_} NAME={name} TYPE={type_}")
            
except Exception as e:
    print(f"Error: {e}")
