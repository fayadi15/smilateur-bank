from bs4 import BeautifulSoup
import os

html_path = 'data/attijari_inspect.html'
if not os.path.exists(html_path):
    print(f"Error: {html_path} not found.")
    exit(1)

soup = BeautifulSoup(open(html_path, encoding='utf-8').read(), 'html.parser')

print("--- CREDIT TYPES (ID=type_credit) ---")
for o in soup.select('select#type_credit option'):
    val = o.get('value')
    text = o.text.strip()
    print(f"VAL={val} TEXT={text}")

print("\n--- FINANCEMENT TYPES (ID=type_financement) ---")
for o in soup.select('select#type_financement option'):
    val = o.get('value')
    text = o.text.strip()
    print(f"VAL={val} TEXT={text}")

# Also look for other inputs like montant, salaire, etc.
print("\n--- OTHER INPUTS ---")
for inp in soup.select('input[type="text"], input[type="number"]'):
    print(f"TAG=input ID={inp.get('id')} NAME={inp.get('name')} TYPE={inp.get('type')}")
