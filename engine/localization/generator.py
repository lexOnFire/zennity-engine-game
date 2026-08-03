"""Typed API Generator for Locale Keys."""
import json
import re
from pathlib import Path

def generate_keys_file(locales_dir: Path, output_file: Path, base_locale: str = "en-US"):
    """Parses all base JSON files and generates a strictly typed LocaleKeys class."""
    base_dir = locales_dir / base_locale
    if not base_dir.exists():
        print(f"Base locale {base_locale} not found.")
        return
        
    all_keys = []
    
    for file in base_dir.rglob("*.json"):
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                all_keys.extend(data.keys())
                
    # Sort and remove duplicates
    all_keys = sorted(list(set(all_keys)))
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write('"""AUTO-GENERATED: Do not edit manually.\n')
        f.write('Run engine/localization/generator.py to update."""\n\n')
        f.write('class LocaleKeys:\n')
        
        if not all_keys:
            f.write('    pass\n')
            
        for key in all_keys:
            # Convert dot notation to upper snake case
            const_name = re.sub(r'[^a-zA-Z0-9]', '_', key).upper()
            f.write(f'    {const_name} = "{key}"\n')
            
    print(f"Generated {len(all_keys)} keys in {output_file}")

if __name__ == "__main__":
    locales = Path(__file__).parent.parent.parent / "locales"
    out = Path(__file__).parent / "keys.py"
    generate_keys_file(locales, out)
