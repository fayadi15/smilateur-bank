import os

file_path = "data/run_final_v2.log"
try:
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        print("".join(lines[-20:]))
except Exception as e:
    try:
         # Fallback for encoding
         with open(file_path, "r", encoding="cp1252") as f:
            lines = f.readlines()
            print("".join(lines[-20:]))
    except:
        print(f"Error reading file: {e}")
