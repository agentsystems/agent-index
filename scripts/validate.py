#!/usr/bin/env python3
"""
Validation script for agent-index repository.

This script validates agent directories and YAML files against JSON schemas
to check file structure and required fields before building the index.

Structure validated:
    developers/{username}/
        profile.yaml                    # Against developer.schema.json
        agents/{agent-name}/
            agent.yaml                  # Against agent-identity.schema.json
            versions.yaml               # Against versions.schema.json
            {version}.yaml              # Against agent-version.schema.json (0.1.0.yaml, etc.)

File type restrictions:
    - Only .yaml files allowed (lowercase extension required, case-sensitive)
    - No hidden files (no files starting with .)
    - No symbolic links
    - Max 100 KB per YAML file
    - Max 10 MB total per developer folder

Note: This validation checks syntax and schema compliance but does
not verify agent functionality, quality, or security.

Usage:
    python validate.py developers              # Validate all developer profiles
    python validate.py agents                  # Validate all agent definitions
    python validate.py all                     # Validate everything
    python validate.py developers/username     # Validate specific developer folder
"""

import json
import re
import sys
from pathlib import Path
from typing import List, Tuple

import yaml
from jsonschema import Draft7Validator, ValidationError

# GitHub username validation (alphanumeric with hyphens)
VALID_DEVELOPER_NAME = re.compile(r'^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?$')

# YAML size and complexity limits
MAX_YAML_SIZE = 100 * 1024  # 100 KB per file
MAX_YAML_COMPLEXITY = 1000  # Max nodes in YAML tree

# File type restrictions
ALLOWED_FILE_EXTENSIONS = {'.yaml'}

# File size limits
MAX_DEVELOPER_FOLDER_SIZE = 10 * 1024 * 1024  # 10 MB total per developer


def load_schema(schema_path: Path) -> dict:
    """Load a JSON schema file."""
    with open(schema_path, 'r') as f:
        return json.load(f)


def count_nodes(obj, count=0) -> int:
    """
    Recursively count nodes in a data structure.

    Returns:
        Total number of nodes (dict keys, list items, scalars)
    """
    if isinstance(obj, dict):
        return sum(count_nodes(v) for v in obj.values()) + len(obj)
    elif isinstance(obj, list):
        return sum(count_nodes(item) for item in obj) + len(obj)
    else:
        return 1


def load_yaml(yaml_path: Path) -> dict:
    """
    Load a YAML file with size and complexity validation.

    Raises:
        ValueError: If file exceeds size or complexity limits
    """
    # Check file size before loading
    file_size = yaml_path.stat().st_size
    if file_size > MAX_YAML_SIZE:
        raise ValueError(
            f"YAML file too large: {file_size} bytes (max {MAX_YAML_SIZE})"
        )

    with open(yaml_path, 'r') as f:
        data = yaml.safe_load(f)

    # Check complexity after parsing to detect exponential expansion
    node_count = count_nodes(data)
    if node_count > MAX_YAML_COMPLEXITY:
        raise ValueError(
            f"YAML too complex: {node_count} nodes (max {MAX_YAML_COMPLEXITY})"
        )

    return data


def validate_file_types_and_sizes(developer_folder: Path) -> List[str]:
    """
    Validate file types and sizes in a developer folder.

    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    total_size = 0

    for file_path in developer_folder.rglob('*'):
        # Reject symbolic links (not permitted)
        if file_path.is_symlink():
            errors.append(
                f"  - {file_path.relative_to(developer_folder)}: "
                f"Symbolic links not allowed"
            )
            continue

        if not file_path.is_file():
            continue

        # Reject ALL hidden files (no exceptions - no .gitkeep, no .gitignore)
        if file_path.name.startswith('.'):
            errors.append(
                f"  - {file_path.relative_to(developer_folder)}: "
                f"Hidden files not allowed"
            )
            continue

        # Case-sensitive extension check (must be exactly .yaml, not .YAML or .YaML)
        ext = file_path.suffix
        file_size = file_path.stat().st_size
        total_size += file_size

        # Check file extension
        if ext not in ALLOWED_FILE_EXTENSIONS:
            errors.append(
                f"  - {file_path.relative_to(developer_folder)}: "
                f"Disallowed file type '{ext}' (only lowercase .yaml extension allowed)"
            )
            continue

    # Check total developer folder size
    if total_size > MAX_DEVELOPER_FOLDER_SIZE:
        errors.append(
            f"  - Total folder size {total_size} bytes exceeds limit "
            f"({MAX_DEVELOPER_FOLDER_SIZE} bytes = {MAX_DEVELOPER_FOLDER_SIZE // (1024*1024)} MB)"
        )

    return errors


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

        # Validate folder name format (GitHub username rules)
        if not VALID_DEVELOPER_NAME.match(developer_name):
            print(f"\n❌ {profile_file.relative_to(base_path)}")
            print(f"  - Invalid folder name format: '{developer_name}'")
            print(f"  - Must match GitHub username rules: ^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?$")
            print(f"  - Start/end with alphanumeric, middle can contain hyphens")
            error_count += 1
            continue

        # Check file types and sizes BEFORE reading files
        file_type_errors = validate_file_types_and_sizes(profile_file.parent)
        if file_type_errors:
            print(f"\n❌ {profile_file.relative_to(base_path)}")
            for error in file_type_errors:
                print(error)
            error_count += 1
            continue

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
    Validate agent directories with identity + version files.

    Args:
        base_path: Repository root path
        developer_folder: Optional specific developer folder name to validate

    Returns:
        Tuple of (valid_count, error_count)
    """
    print("\n" + "="*70)
    print("VALIDATING AGENT DEFINITIONS")
    print("="*70)

    # Load schemas
    identity_schema_path = base_path / "schema" / "agent-identity.schema.json"
    versions_schema_path = base_path / "schema" / "versions.schema.json"
    version_schema_path = base_path / "schema" / "agent-version.schema.json"
    identity_schema = load_schema(identity_schema_path)
    versions_schema = load_schema(versions_schema_path)
    version_schema = load_schema(version_schema_path)
    identity_validator = Draft7Validator(identity_schema)
    versions_validator = Draft7Validator(versions_schema)
    version_validator = Draft7Validator(version_schema)

    developers_path = base_path / "developers"

    # Find agent directories
    if developer_folder:
        agents_path = developers_path / developer_folder / "agents"
        if not agents_path.exists():
            print(f"\nNo agents folder found for {developer_folder}.")
            return 0, 0
        agent_dirs = [d for d in agents_path.iterdir() if d.is_dir()]
    else:
        agent_dirs = []
        for dev_dir in developers_path.iterdir():
            if not dev_dir.is_dir():
                continue
            agents_path = dev_dir / "agents"
            if agents_path.exists():
                agent_dirs.extend([d for d in agents_path.iterdir() if d.is_dir()])

    if not agent_dirs:
        print("\nNo agent directories found.")
        return 0, 0

    valid_count = 0
    error_count = 0

    for agent_dir in sorted(agent_dirs):
        developer_name = agent_dir.parent.parent.name
        agent_name = agent_dir.name
        has_errors = False
        all_errors = []

        # Check file types and sizes BEFORE reading files
        file_type_errors = validate_file_types_and_sizes(agent_dir)
        if file_type_errors:
            print(f"\n❌ {agent_dir.relative_to(base_path)}/")
            for error in file_type_errors:
                print(error)
            error_count += 1
            continue

        # Validate agent.yaml (identity)
        agent_yaml = agent_dir / "agent.yaml"
        if not agent_yaml.exists():
            print(f"\n❌ {agent_dir.relative_to(base_path)}")
            print(f"  - Missing agent.yaml file")
            error_count += 1
            continue

        identity_data = load_yaml(agent_yaml)

        # Check developer field matches folder
        if identity_data.get('developer') != developer_name:
            all_errors.append(
                f"  - agent.yaml: developer field '{identity_data.get('developer')}' "
                f"doesn't match folder '{developer_name}'"
            )
            has_errors = True

        # Check name field matches directory
        if identity_data.get('name') != agent_name:
            all_errors.append(
                f"  - agent.yaml: name field '{identity_data.get('name')}' "
                f"doesn't match directory '{agent_name}'"
            )
            has_errors = True

        # Validate identity against schema
        identity_errors = validate_file(agent_yaml, identity_schema, identity_validator)
        if identity_errors:
            all_errors.extend([f"  - agent.yaml{e.lstrip('  -')}" for e in identity_errors])
            has_errors = True

        # Validate versions.yaml
        versions_yaml = agent_dir / "versions.yaml"
        if not versions_yaml.exists():
            all_errors.append(f"  - Missing versions.yaml file")
            has_errors = True
        else:
            versions_management = load_yaml(versions_yaml)

            # Validate versions.yaml against schema
            versions_errors = validate_file(versions_yaml, versions_schema, versions_validator)
            if versions_errors:
                all_errors.extend([f"  - versions.yaml{e.lstrip('  -')}" for e in versions_errors])
                has_errors = True

            # Check that 'latest_version' field points to existing version file
            latest_version = versions_management.get('latest_version')
            if latest_version:
                latest_version_file = agent_dir / f"{latest_version}.yaml"
                if not latest_version_file.exists():
                    all_errors.append(
                        f"  - versions.yaml: latest_version '{latest_version}' "
                        f"does not match any version file ({latest_version}.yaml not found)"
                    )
                    has_errors = True

            # Check that all listed_versions point to existing files
            listed_versions = versions_management.get('listed_versions', [])
            for listed_version in listed_versions:
                listed_version_file = agent_dir / f"{listed_version}.yaml"
                if not listed_version_file.exists():
                    all_errors.append(
                        f"  - versions.yaml: listed_versions contains '{listed_version}' "
                        f"but {listed_version}.yaml not found"
                    )
                    has_errors = True

        # Find and validate version files
        # Exclude agent.yaml and versions.yaml, match version files like 0.1.0.yaml
        version_files = sorted([f for f in agent_dir.glob("*.yaml")
                               if f.name not in ['agent.yaml', 'versions.yaml']])
        if not version_files:
            all_errors.append(f"  - No version files found (e.g., 0.1.0.yaml)")
            has_errors = True
        else:
            for version_file in version_files:
                version_data = load_yaml(version_file)

                # Check version matches filename
                file_version = version_file.stem
                data_version = version_data.get('version', '')
                if data_version != file_version:
                    all_errors.append(
                        f"  - {version_file.name}: version field '{data_version}' "
                        f"doesn't match filename (expected '{file_version}')"
                    )
                    has_errors = True

                # Validate version against schema
                version_errors = validate_file(version_file, version_schema, version_validator)
                if version_errors:
                    all_errors.extend([f"  - {version_file.name}{e.lstrip('  -')}" for e in version_errors])
                    has_errors = True

        if has_errors:
            print(f"\n❌ {agent_dir.relative_to(base_path)}/")
            for error in all_errors:
                print(error)
            error_count += 1
        else:
            print(f"✅ {agent_dir.relative_to(base_path)}/ ({len(version_files)} versions)")
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
