"""Unit Tests for Key Generator."""
import pytest
from pathlib import Path
from engine.localization.generator import generate_keys_file
import tempfile
import json
import os

def test_generate_keys():
    with tempfile.TemporaryDirectory() as tmpdir:
        locales = Path(tmpdir) / "locales"
        en_us = locales / "en-US"
        en_us.mkdir(parents=True)
        
        with open(en_us / "test.json", "w") as f:
            json.dump({"my.test.key": "Value"}, f)
            
        out_file = Path(tmpdir) / "keys.py"
        generate_keys_file(locales, out_file)
        
        assert out_file.exists()
        content = out_file.read_text()
        assert 'MY_TEST_KEY = "my.test.key"' in content
