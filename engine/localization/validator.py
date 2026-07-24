"""Localization Validator CLI."""
import json
import sys
from pathlib import Path
from typing import Dict, Set

def load_keys(directory: Path) -> Set[str]:
    keys = set()
    if not directory.exists():
        return keys
    for file in directory.glob("*.json"):
        try:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    keys.update(data.keys())
        except Exception as e:
            print(f"Error reading {file}: {e}")
    return keys

def run_validation(locales_dir: Path, base_locale: str = "en-US") -> bool:
    base_dir = locales_dir / base_locale
    if not base_dir.exists():
        print(f"Base locale {base_locale} not found in {locales_dir}")
        return False
        
    base_keys = load_keys(base_dir)
    print(f"Found {len(base_keys)} keys in base locale ({base_locale})")
    
    success = True
    for loc_dir in locales_dir.iterdir():
        if loc_dir.is_dir() and loc_dir.name != base_locale:
            print(f"\nChecking locale: {loc_dir.name}")
            loc_keys = load_keys(loc_dir)
            missing = base_keys - loc_keys
            orphan = loc_keys - base_keys
            
            if missing:
                success = False
                print(f"  Missing {len(missing)} keys:")
                for k in list(missing)[:10]:
                    print(f"    - {k}")
                if len(missing) > 10: print("    ... and more")
            
            if orphan:
                print(f"  Warning: Found {len(orphan)} orphan keys (not in base):")
                for k in list(orphan)[:5]:
                    print(f"    - {k}")
                    
            if not missing and not orphan:
                print("  Perfect match!")
                
    return success

if __name__ == "__main__":
    locales_path = Path(__file__).parent.parent.parent / "locales"
    if run_validation(locales_path):
        print("\nValidation Passed.")
        sys.exit(0)
    else:
        print("\nValidation Failed.")
        sys.exit(1)
