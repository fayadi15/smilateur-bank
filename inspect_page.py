import requests
import re

url = "https://www.banquezitouna.com/fr/particuliers/simulateur"
try:
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    html = response.text
    
    print("Successfully fetched page.")
    
    # Simple Regex to find inputs and selects
    print("\n--- INPUTS ---")
    inputs = re.findall(r'<input[^>]*>', html)
    for inp in inputs:
        if 'hidden' not in inp:
            print(inp)
            
    print("\n--- SELECTS ---")
    selects = re.findall(r'<select[^>]*>.*?</select>', html, re.DOTALL)
    # The regex for select might be too greedy or miss if multiline, let's just find the opening tag
    select_tags = re.findall(r'<select[^>]*>', html)
    for sel in select_tags:
        print(sel)
        
    print("\n--- BUTTONS ---")
    buttons = re.findall(r'<button[^>]*>', html)
    for btn in buttons:
        print(btn)

    print("\n--- POSSIBLE RESULT CONTAINERS ---")
    # Looking for divs that might contain results
    divs = re.findall(r'<div[^>]*id="[^"]*result[^"]*"[^>]*>', html, re.IGNORECASE)
    for d in divs:
        print(d)

except Exception as e:
    print(f"Error: {e}")
