"""Advanced Localization Validator CLI."""
import json
import sys
import re
from pathlib import Path
from typing import Dict, Set

# Attempt to load LocaleKeys to validate it
try:
    from engine.localization.keys import LocaleKeys
    KEYS_CLASS_LOADED = True
except ImportError:
    KEYS_CLASS_LOADED = False

def extract_placeholders(text: str) -> Set[str]:
    return set(re.findall(r'\{([^}]+)\}', text))

def load_translations(directory: Path) -> Dict[str, str]:
    translations = {}
    if not directory.exists():
        return translations
    for file in directory.rglob("*.json"):
        try:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    for k, v in data.items():
                        if k in translations:
                            print(f"[Warning] Duplicate key '{k}' found in {file.name}")
                        translations[k] = str(v)
        except Exception as e:
            print(f"[Error] reading {file}: {e}")
    return translations

def run_validation(locales_dir: Path, base_locale: str = "en-US") -> bool:
    base_dir = locales_dir / base_locale
    if not base_dir.exists():
        print(f"Base locale {base_locale} not found in {locales_dir}")
        return False
        
    base_trans = load_translations(base_dir)
    base_keys = set(base_trans.keys())
    total_base = len(base_keys)
    
    if total_base == 0:
        print("No keys found to validate.")
        return True
        
    success = True
    
    # 1. Validate LocaleKeys Class Synchronization
    if KEYS_CLASS_LOADED:
        class_keys = set(v for k, v in LocaleKeys.__dict__.items() if not k.startswith("__"))
        if class_keys != base_keys:
            success = False
            missing_in_class = base_keys - class_keys
            missing_in_json = class_keys - base_keys
            print("\n[ERROR] LocaleKeys class is out of sync with JSON files!")
            if missing_in_class: print(f"  Missing in LocaleKeys: {missing_in_class}")
            if missing_in_json: print(f"  Missing in JSON files: {missing_in_json}")
    else:
        print("\n[WARNING] LocaleKeys not generated. Run generator.py.")
        
    # 2. Validate Locales
    for loc_dir in locales_dir.iterdir():
        if loc_dir.is_dir() and loc_dir.name != base_locale:
            print(f"\n--- Validating Locale: {loc_dir.name} ---")
            loc_trans = load_translations(loc_dir)
            loc_keys = set(loc_trans.keys())
            
            missing = base_keys - loc_keys
            orphan = loc_keys - base_keys
            
            coverage = ((total_base - len(missing)) / total_base) * 100
            print(f"Coverage: {coverage:.2f}%")
            
            if missing:
                success = False
                print(f"  Missing {len(missing)} keys. Sample:")
                for k in list(missing)[:5]: print(f"    - {k}")
            
            placeholder_mismatch = 0
            empty_values = 0
            
            for k, v in loc_trans.items():
                if k not in base_trans:
                    continue
                if not v.strip():
                    empty_values += 1
                    success = False
                    
                base_placeholders = extract_placeholders(base_trans[k])
                loc_placeholders = extract_placeholders(v)
                
                if base_placeholders != loc_placeholders:
                    success = False
                    placeholder_mismatch += 1
                    print(f"  Placeholder Mismatch for '{k}': Base={base_placeholders} vs Target={loc_placeholders}")
                    
            if empty_values > 0: print(f"  Found {empty_values} empty values.")
            if orphan: print(f"  Warning: Found {len(orphan)} orphan keys.")
                
    return success

if __name__ == "__main__":
    locales_path = Path(__file__).parent.parent.parent / "locales"
    if run_validation(locales_path):
        print("\nValidation Passed.")
        sys.exit(0)
    else:
        print("\nValidation Failed.")
        sys.exit(1)
