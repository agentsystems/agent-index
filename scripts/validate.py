#!/usr/bin/env python3
"""
Validation script for agent-index repository.

This script validates YAML files against JSON schemas to check
file structure and required fields before building the index.

Note: This validation checks syntax and schema compliance but does
not verify agent functionality, quality, or security.

Usage:
    python validate.py developers              # Validate all developer profiles
    python validate.py agents                  # Validate all agent definitions
    python validate.py all                     # Validate everything
    python validate.py developers/username     # Validate specific developer folder
"""

import json
import sys
from pathlib import Path
from typing import List, Tuple

import yaml
from jsonschema import Draft7Validator, ValidationError


def load_schema(schema_path: Path) -> dict:
    """Load a JSON schema file."""
    with open(schema_path, 'r') as f:
        return json.load(f)


def load_yaml(yaml_path: Path) -> dict:
    """Load a YAML file."""
    with open(yaml_path, 'r') as f:
        return yaml.safe_load(f)


def validate_file(yaml_path: Path, schema: dict, validator: Draft7Validator) -> List[str]:
    """
    Validate a single YAML file against a schema.

    Returns:
        List of error messages (empty if valid)
    """
    errors = []

    try:
        data = load_yaml(yaml_path)

        # Validate against schema
        validation_errors = list(validator.iter_errors(data))

        if validation_errors:
            for error in validation_errors:
                path = ".".join(str(p) for p in error.path) if error.path else "root"
                errors.append(f"  - {path}: {error.message}")

    except yaml.YAMLError as e:
        errors.append(f"  - YAML parsing error: {e}")
    except Exception as e:
        errors.append(f"  - Unexpected error: {e}")

    return errors


def validate_developers(base_path: Path, developer_folder: str = None) -> Tuple[int, int]:
    """
    Validate developer profile.yaml files.

    Args:
        base_path: Repository root path
        developer_folder: Optional specific developer folder name to validate

    Returns:
        Tuple of (valid_count, error_count)
    """
    print("\n" + "="*70)
    print("VALIDATING DEVELOPER PROFILES")
    print("="*70)

    schema_path = base_path / "schema" / "developer.schema.json"
    schema = load_schema(schema_path)
    validator = Draft7Validator(schema)

    developers_path = base_path / "developers"

    if developer_folder:
        # Validate specific developer folder
        profile_files = [developers_path / developer_folder / "profile.yaml"]
        if not profile_files[0].exists():
            print(f"\n⚠️  No profile.yaml found in {developer_folder}")
            return 0, 0
    else:
        # Validate all developers
        profile_files = list(developers_path.glob("*/profile.yaml"))

    if not profile_files:
        print("\nNo developer profiles found.")
        return 0, 0

    valid_count = 0
    error_count = 0

    for profile_file in sorted(profile_files):
        developer_name = profile_file.parent.name

        # Validate that folder name matches developer field
        data = load_yaml(profile_file)
        developer_field = data.get('developer', '')

        if developer_name != developer_field:
            print(f"\n❌ {profile_file.relative_to(base_path)}")
            print(f"  - Folder name is '{developer_name}' but profile.yaml has developer: '{developer_field}'")
            print(f"  - These must match exactly (folder ownership is checked via fork owner)")
            error_count += 1
            continue

        errors = validate_file(profile_file, schema, validator)

        if errors:
            print(f"\n❌ {profile_file.relative_to(base_path)}")
            for error in errors:
                print(error)
            error_count += 1
        else:
            print(f"✅ {profile_file.relative_to(base_path)}")
            valid_count += 1

    return valid_count, error_count


def validate_agents(base_path: Path, developer_folder: str = None) -> Tuple[int, int]:
    """
    Validate agent YAML files.

    Args:
        base_path: Repository root path
        developer_folder: Optional specific developer folder name to validate

    Returns:
        Tuple of (valid_count, error_count)
    """
    print("\n" + "="*70)
    print("VALIDATING AGENT DEFINITIONS")
    print("="*70)

    schema_path = base_path / "schema" / "agent.schema.json"
    schema = load_schema(schema_path)
    validator = Draft7Validator(schema)

    developers_path = base_path / "developers"

    if developer_folder:
        # Validate specific developer folder
        agent_files = list((developers_path / developer_folder / "agents").glob("*.yaml"))
    else:
        # Validate all developers
        agent_files = list(developers_path.glob("*/agents/*.yaml"))

    if not agent_files:
        print("\nNo agent definitions found.")
        return 0, 0

    valid_count = 0
    error_count = 0

    for agent_file in sorted(agent_files):
        developer_name = agent_file.parent.parent.name

        # Validate that developer field matches folder name
        data = load_yaml(agent_file)
        agent_developer = data.get('developer', '')

        if developer_name != agent_developer:
            print(f"\n❌ {agent_file.relative_to(base_path)}")
            print(f"  - Agent has developer: '{agent_developer}' but is in folder 'developers/{developer_name}/'")
            print(f"  - The developer field must match the folder name exactly")
            error_count += 1
            continue

        errors = validate_file(agent_file, schema, validator)

        if errors:
            print(f"\n❌ {agent_file.relative_to(base_path)}")
            for error in errors:
                print(error)
            error_count += 1
        else:
            print(f"✅ {agent_file.relative_to(base_path)}")
            valid_count += 1

    return valid_count, error_count


def main():
    """Main validation entry point."""
    if len(sys.argv) < 2:
        print("Usage: python validate.py [developers|agents|all|developers/username]")
        sys.exit(1)

    arg = sys.argv[1]
    base_path = Path(__file__).parent.parent

    # Check if argument is a specific developer folder path
    if arg.startswith("developers/"):
        developer_folder = arg.split("/", 1)[1]
        print(f"\n🔍 Validating specific developer: {developer_folder}")

        total_valid = 0
        total_errors = 0

        valid, errors = validate_developers(base_path, developer_folder)
        total_valid += valid
        total_errors += errors

        valid, errors = validate_agents(base_path, developer_folder)
        total_valid += valid
        total_errors += errors

    else:
        # Standard mode: developers, agents, or all
        mode = arg.lower()
        total_valid = 0
        total_errors = 0

        if mode in ["developers", "all"]:
            valid, errors = validate_developers(base_path)
            total_valid += valid
            total_errors += errors

        if mode in ["agents", "all"]:
            valid, errors = validate_agents(base_path)
            total_valid += valid
            total_errors += errors

    # Print summary
    print("\n" + "="*70)
    print("VALIDATION SUMMARY")
    print("="*70)
    print(f"✅ Valid files:   {total_valid}")
    print(f"❌ Invalid files: {total_errors}")
    print("="*70 + "\n")

    if total_errors > 0:
        sys.exit(1)

    print("🎉 All validations passed!\n")
    sys.exit(0)


if __name__ == "__main__":
    main()
