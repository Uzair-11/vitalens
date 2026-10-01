import re
from app.ml.lab_extractor import get_canonical_biomarkers, parse_range_string, evaluate_flag

line = "TSH (Thyroid Stimulating Hormone) 6.8 HIGH 0.4 - 4.0 uIU/mL"
line_alt = "ALT (Alanine Aminotransferase) 58.0 HIGH 7 - 56 U/L"
line_hb = "Hemoglobin 10.9 LOW 12.0 - 15.5 g/dL"
line_plt = "Platelets 260 150 - 450 x10E3/uL"

lib = get_canonical_biomarkers()

for test_line in [line, line_alt, line_hb, line_plt]:
    print(f"\nTesting line: {test_line}")
    matched = False
    for key, meta in lib.items():
        for alias in meta.get("aliases", []):
            pattern = r"\b" + re.escape(alias) + r"[\s:=-]+([\d\.]+)\s*([a-zA-Z/%^0-9]*)\s*(?:\(?\s*([\d\.\s<>-]+)\s*\)?)?"
            m = re.search(pattern, test_line.lower())
            if m:
                print(f"  MATCHED alias '{alias}' for key '{key}': groups = {m.groups()}")
                matched = True
                break
        if matched:
            break
    if not matched:
        print("  NO MATCH!")
