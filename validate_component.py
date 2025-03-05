import os
import sys
import json
import importlib.util
import re
from pathlib import Path

def validate_manifest(root_dir):
    """Validate manifest.json file"""
    manifest_path = os.path.join(root_dir, "custom_components", "mitsubishi_heavy_ac", "manifest.json")
    
    if not os.path.exists(manifest_path):
        print("❌ ERROR: manifest.json not found")
        return False
    
    try:
        with open(manifest_path) as f:
            manifest = json.load(f)
        
        required_keys = ["domain", "name", "documentation", "dependencies", "codeowners", "version"]
        for key in required_keys:
            if key not in manifest:
                print(f"❌ ERROR: '{key}' missing from manifest.json")
                return False
                
        print("✅ manifest.json validated successfully")
        return True
    except json.JSONDecodeError:
        print("❌ ERROR: Invalid JSON in manifest.json")
        return False

def validate_python_files(root_dir):
    """Check Python syntax in all component files"""
    component_dir = os.path.join(root_dir, "custom_components", "mitsubishi_heavy_ac")
    
    if not os.path.exists(component_dir):
        print("❌ ERROR: Component directory not found")
        return False
        
    all_valid = True
    for root, _, files in os.walk(component_dir):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r") as f:
                        source = f.read()
                    compile(source, file_path, "exec")
                    print(f"✅ {os.path.relpath(file_path, root_dir)} - Syntax OK")
                except SyntaxError as e:
                    print(f"❌ {os.path.relpath(file_path, root_dir)} - Syntax Error: {e}")
                    all_valid = False
    
    return all_valid

def check_ha_imports(root_dir):
    """Check for deprecated Home Assistant imports and patterns"""
    component_dir = os.path.join(root_dir, "custom_components", "mitsubishi_heavy_ac")
    deprecated_patterns = [
        (r"import homeassistant.remote", "Remote API is deprecated"),
        (r"from homeassistant.const import TEMP_CELSIUS", "Use UnitOfTemperature.CELSIUS instead"),
        (r"async_track_point_in_time\(", "Check for uncancelled listeners"),
    ]
    
    issues_found = False
    for root, _, files in os.walk(component_dir):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r") as f:
                        content = f.read()
                    
                    for pattern, message in deprecated_patterns:
                        if re.search(pattern, content):
                            print(f"⚠️ {os.path.relpath(file_path, root_dir)} - {message}")
                            issues_found = True
                            
                except Exception as e:
                    print(f"❌ Error checking {file_path}: {e}")
    
    if not issues_found:
        print("✅ No deprecated imports or patterns found")
    
    return not issues_found

def validate_translations(root_dir):
    """Validate the translations folder structure"""
    translations_dir = os.path.join(root_dir, "custom_components", "mitsubishi_heavy_ac", "translations")
    
    if not os.path.exists(translations_dir):
        print("⚠️ No translations directory found")
        return True
    
    en_file = os.path.join(translations_dir, "en.json")
    if not os.path.exists(en_file):
        print("⚠️ No en.json translation file found")
        return False
        
    try:
        with open(en_file) as f:
            en_data = json.load(f)
        print("✅ English translations validated")
        return True
    except json.JSONDecodeError:
        print("❌ ERROR: Invalid JSON in en.json translations file")
        return False

def main():
    root_dir = os.path.dirname(os.path.realpath(__file__))
    print(f"Validating component in: {root_dir}")
    
    manifest_valid = validate_manifest(root_dir)
    python_valid = validate_python_files(root_dir)
    imports_valid = check_ha_imports(root_dir)
    translations_valid = validate_translations(root_dir)
    
    print("\n=== Validation Summary ===")
    if all([manifest_valid, python_valid, imports_valid, translations_valid]):
        print("✅ All checks passed!")
    else:
        print("❌ Some checks failed. See details above.")

if __name__ == "__main__":
    main()
