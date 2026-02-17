from bs4 import BeautifulSoup
import os

file_path = "data/debug_page.html"

if not os.path.exists(file_path):
    print(f"File {file_path} not found yet.")
else:
    with open(file_path, "r", encoding="utf-8") as f:
        html = f.read()

    soup = BeautifulSoup(html, 'html.parser')

    print("--- SUBMIT BUTTON SEARCH ---")
    # Finding by text
    for tag in soup.find_all(string=lambda text: "simuler" in text.lower() if text else False):
        parent = tag.parent
        print(f"TEXT MATCH: Tag='{parent.name}' Text='{tag.strip()}' Class='{parent.get('class')}' ID='{parent.get('id')}'")

    # Finding buttons
    for btn in soup.find_all('button'):
        print(f"BUTTON: Text='{btn.text.strip()}' Class='{btn.get('class')}' ID='{btn.get('id')}'")
        
    # Finding inputs type submit/button
    for inp in soup.find_all('input', type=['submit', 'button']):
        print(f"INPUT: Type='{inp.get('type')}' Value='{inp.get('value')}' Class='{inp.get('class')}' ID='{inp.get('id')}'")
