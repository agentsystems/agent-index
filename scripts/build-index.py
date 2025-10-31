#!/usr/bin/env python3
"""
Build script for agent-index repository.

This script processes agent directories from developers/ and generates
a structured JSON index that can be served via GitHub Pages.

Input structure:
    developers/{username}/
        profile.yaml                        # Developer profile
        agents/{agent-name}/
            agent.yaml                      # Agent identity (never changes)
            versions.yaml                   # Version management (latest, listed_versions)
            {version}.yaml                  # Version specifications (0.1.0.yaml, 0.2.0.yaml, etc.)

Output structure:
    dist/
        index.json                          # Main index of all agents
        developers.json                     # List of all developers
        @{developer}/
            profile.json                    # Developer profile
            agents.json                     # List of developer's agents
            {agent}/
                metadata.json               # Agent metadata (latest version)
                {version}/
                    metadata.json           # Version-specific metadata

Usage:
    python build-index.py
"""

import json
import shutil
from datetime import datetime, UTC
from pathlib import Path
from typing import Any, Dict, List

import yaml

# YAML size and complexity limits to help mitigate resource exhaustion attacks
MAX_YAML_SIZE = 100 * 1024  # 100 KB per file
MAX_YAML_COMPLEXITY = 1000  # Max nodes in YAML tree


class IndexBuilder:
    """Builds the agent index from YAML source files."""

    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.developers_path = base_path / "developers"
        self.dist_path = base_path / "dist"
        self.developers: Dict[str, Any] = {}
        self.agents: List[Dict[str, Any]] = []
        self.failed_developers: int = 0
        self.failed_agents: int = 0

    def clean_dist(self):
        """Remove and recreate the dist directory."""
        if self.dist_path.exists():
            shutil.rmtree(self.dist_path)
        self.dist_path.mkdir(parents=True)

    def count_nodes(self, obj) -> int:
        """
        Recursively count nodes in a data structure.

        Returns:
            Total number of nodes (dict keys, list items, scalars)
        """
        if isinstance(obj, dict):
            return sum(self.count_nodes(v) for v in obj.values()) + len(obj)
        elif isinstance(obj, list):
            return sum(self.count_nodes(item) for item in obj) + len(obj)
        else:
            return 1

    def load_yaml(self, yaml_path: Path) -> Dict[str, Any]:
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
        node_count = self.count_nodes(data)
        if node_count > MAX_YAML_COMPLEXITY:
            raise ValueError(
                f"YAML too complex: {node_count} nodes (max {MAX_YAML_COMPLEXITY})"
            )

        return data

    def save_json(self, data: Any, output_path: Path):
        """Save data as formatted JSON."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def process_developer(self, developer_dir: Path) -> Dict[str, Any]:
        """Process a single developer directory."""
        developer_name = developer_dir.name
        profile_path = developer_dir / "profile.yaml"

        if not profile_path.exists():
            raise FileNotFoundError(f"Missing profile.yaml for {developer_name}")

        profile_data = self.load_yaml(profile_path)

        # Validate developer field matches folder name
        if profile_data.get('developer') != developer_name:
            raise ValueError(
                f"developer '{profile_data.get('developer')}' "
                f"does not match folder name '{developer_name}'"
            )

        # Add computed fields
        profile_data['_id'] = developer_name
        profile_data['_agent_count'] = 0  # Will be updated later

        return profile_data

    def process_agent(
        self,
        agent_dir: Path,
        developer_name: str
    ) -> Dict[str, Any]:
        """Process a single agent directory with identity + version files."""
        agent_name = agent_dir.name

        # Read agent identity
        agent_yaml_path = agent_dir / "agent.yaml"
        if not agent_yaml_path.exists():
            raise FileNotFoundError(f"Missing agent.yaml in {developer_name}/agents/{agent_name}")

        identity_data = self.load_yaml(agent_yaml_path)

        # Validate developer field matches folder name
        if identity_data.get('developer') != developer_name:
            raise ValueError(
                f"Agent developer field '{identity_data.get('developer')}' "
                f"does not match folder '{developer_name}'"
            )

        # Validate name matches directory
        if identity_data.get('name') != agent_name:
            raise ValueError(
                f"Agent name '{identity_data.get('name')}' "
                f"does not match directory name '{agent_name}'"
            )

        # Read version management
        versions_yaml_path = agent_dir / "versions.yaml"
        if not versions_yaml_path.exists():
            raise FileNotFoundError(f"Missing versions.yaml in {developer_name}/agents/{agent_name}")

        versions_data = self.load_yaml(versions_yaml_path)
        latest_version_string = versions_data.get('latest_version')
        listed_versions = versions_data.get('listed_versions', [])

        if not latest_version_string:
            raise ValueError(f"Agent {developer_name}/{agent_name} missing 'latest_version' field in versions.yaml")

        # Read the latest version file
        latest_version_file = agent_dir / f"{latest_version_string}.yaml"
        if not latest_version_file.exists():
            raise ValueError(
                f"Agent {developer_name}/{agent_name} specifies latest: '{latest_version_string}' "
                f"but {latest_version_string}.yaml does not exist"
            )

        latest_version = self.load_yaml(latest_version_file)

        # Validate version in file matches filename
        file_version = latest_version_file.stem
        data_version = latest_version.get('version', '')
        if data_version != file_version:
            raise ValueError(
                f"Version in {latest_version_file.name} ('{data_version}') "
                f"does not match filename (expected '{file_version}')"
            )

        # Read all version files for available versions list
        # Pattern matches files like 0.1.0.yaml, 1.0.0-beta.1.yaml
        version_files = sorted([f for f in agent_dir.glob("*.yaml")
                               if f.name not in ['agent.yaml', 'versions.yaml']])
        if not version_files:
            raise ValueError(f"Agent {developer_name}/{agent_name} has no version files")

        versions = []
        for version_file in version_files:
            version_data = self.load_yaml(version_file)

            # Validate version in file matches filename
            file_version = version_file.stem
            data_version = version_data.get('version', '')
            if data_version != file_version:
                raise ValueError(
                    f"Version in {version_file.name} ('{data_version}') "
                    f"does not match filename (expected '{file_version}')"
                )

            versions.append(version_data)

        # Build merged data: identity + latest version
        merged_data = {}

        # Copy all version-specific data from latest version
        for key, value in latest_version.items():
            if value is not None:
                merged_data[key] = value

        # Add identity fields
        merged_data['name'] = agent_name
        merged_data['developer'] = developer_name
        merged_data['description'] = identity_data.get('description')
        merged_data['container_image'] = identity_data.get('container_image')
        merged_data['source_repository_url'] = identity_data.get('source_repository_url')
        merged_data['primary_function'] = identity_data.get('primary_function')
        merged_data['tags'] = identity_data.get('tags')
        merged_data['capabilities'] = identity_data.get('capabilities')

        # Auto-derive container tag from version
        container_base = identity_data.get('container_image', '')
        version_tag = latest_version.get('version', '')
        if container_base and version_tag:
            merged_data['container_image_full'] = f"{container_base}:{version_tag}"

        # Add computed fields
        merged_data['_id'] = f"{developer_name}/{agent_name}"
        merged_data['_index_name'] = f"@{developer_name}/{agent_name}"

        # Add available versions list (only listed ones from versions.yaml)
        # Include version-specific requirements so UI can show accurate requirements per version
        available_versions = []
        for version_string in listed_versions:
            # Find the version data
            version_data = next((v for v in versions if v.get('version') == version_string), None)
            if version_data:
                available_versions.append({
                    'version': version_string,
                    'is_latest': version_string == latest_version_string,
                    'readiness_level': version_data.get('readiness_level'),
                    # Include requirements that vary by version
                    'model_dependencies': version_data.get('model_dependencies'),
                    'required_egress': version_data.get('required_egress'),
                })
        merged_data['_available_versions'] = available_versions

        # Agent is listed if it has any listed_versions
        merged_data['_is_listed'] = len(listed_versions) > 0

        return merged_data

    def build_developers(self):
        """Process all developer profiles."""
        print("\n" + "="*70)
        print("PROCESSING DEVELOPERS")
        print("="*70)

        for developer_dir in sorted(self.developers_path.iterdir()):
            if not developer_dir.is_dir():
                continue

            try:
                developer_data = self.process_developer(developer_dir)
                developer_name = developer_data['developer']

                self.developers[developer_name] = developer_data

                # Save individual developer profile
                output_path = self.dist_path / f"@{developer_name}" / "profile.json"
                self.save_json(developer_data, output_path)

                print(f"✅ {developer_name}")

            except Exception as e:
                print(f"❌ {developer_dir.name}: {e}")
                self.failed_developers += 1
                # Continue processing other developers instead of failing entire build
                continue

    def build_agents(self):
        """Process all agent definitions."""
        print("\n" + "="*70)
        print("PROCESSING AGENTS")
        print("="*70)

        for developer_dir in sorted(self.developers_path.iterdir()):
            if not developer_dir.is_dir():
                continue

            developer_name = developer_dir.name
            agents_dir = developer_dir / "agents"

            if not agents_dir.exists():
                continue

            developer_agents = []

            # Iterate through agent directories
            for agent_dir in sorted(agents_dir.iterdir()):
                if not agent_dir.is_dir():
                    continue

                try:
                    agent_data = self.process_agent(agent_dir, developer_name)
                    agent_name = agent_data['name']
                    version = agent_data['version']

                    # Add to global agents list
                    self.agents.append(agent_data)

                    # Add to developer's agents list
                    developer_agents.append({
                        'name': agent_name,
                        'version': version,
                        'description': agent_data.get('description'),
                        '_id': agent_data['_id'],
                        '_index_name': agent_data['_index_name'],
                    })

                    # Save version-specific metadata
                    version_path = (
                        self.dist_path / f"@{developer_name}" / agent_name / version / "metadata.json"
                    )
                    self.save_json(agent_data, version_path)

                    # Save latest metadata (without version in path)
                    latest_path = (
                        self.dist_path / f"@{developer_name}" / agent_name / "metadata.json"
                    )
                    self.save_json(agent_data, latest_path)

                    print(f"✅ @{developer_name}/{agent_name}@{version}")

                except Exception as e:
                    print(f"❌ {agent_dir.name}: {e}")
                    self.failed_agents += 1
                    # Continue processing other agents instead of failing entire build
                    continue

            # Update developer agent count
            if developer_name in self.developers:
                self.developers[developer_name]['_agent_count'] = len(developer_agents)

                # Save developer's agents list
                agents_list_path = self.dist_path / f"@{developer_name}" / "agents.json"
                self.save_json(developer_agents, agents_list_path)

                # Update developer profile with agent count
                profile_path = self.dist_path / f"@{developer_name}" / "profile.json"
                self.save_json(self.developers[developer_name], profile_path)

    def build_indexes(self):
        """Build top-level index files."""
        print("\n" + "="*70)
        print("BUILDING INDEXES")
        print("="*70)

        # Build developers index
        developers_list = [
            {
                'developer': dev['developer'],
                'name': dev['name'],
                'type': dev.get('type'),
                'bio': dev.get('bio'),
                'avatar_url': dev.get('avatar_url'),
                'website': dev.get('website'),
                '_id': dev['_id'],
                '_agent_count': dev['_agent_count'],
            }
            for dev in self.developers.values()
        ]

        developers_index = {
            'developers': developers_list,
            'count': len(developers_list),
            'last_updated': datetime.now(UTC).isoformat().replace('+00:00', 'Z'),
        }

        self.save_json(developers_index, self.dist_path / "developers.json")
        print(f"✅ developers.json ({len(developers_list)} developers)")

        # Build agents index
        agents_list = []
        for agent in self.agents:
            # Only include agents that have listed_versions
            if not agent.get('_is_listed', False):
                continue

            developer_name = agent['developer']
            developer_data = self.developers.get(developer_name, {})

            agents_list.append({
                # Core fields
                'developer': developer_name,
                'name': agent['name'],
                'version': agent['version'],
                'description': agent.get('description'),
                'context': agent.get('context'),
                'primary_function': agent.get('primary_function'),
                'readiness_level': agent.get('readiness_level'),

                # Repository info (needed for install/view source)
                'container_image': agent.get('container_image'),
                'container_image_access': agent.get('container_image_access', 'private'),
                'source_repository_url': agent.get('source_repository_url'),
                'source_repository_access': agent.get('source_repository_access', 'private'),

                # Developer info (for rich cards without extra requests)
                'developer_id': developer_data.get('_id', developer_name),
                'developer_name': developer_data.get('name', developer_name),
                'developer_avatar_url': developer_data.get('avatar_url'),

                # Requirements (shown on cards/modals)
                'model_dependencies': agent.get('model_dependencies'),
                'required_egress': agent.get('required_egress'),

                # Timestamp
                'created_at': agent.get('created_at', datetime.now(UTC).isoformat().replace('+00:00', 'Z')),

                # IDs
                '_id': agent['_id'],
                '_index_name': agent['_index_name'],

                # Version info
                '_available_versions': agent.get('_available_versions', []),
            })

        agents_index = {
            'agents': agents_list,
            'count': len(agents_list),
            'last_updated': datetime.now(UTC).isoformat().replace('+00:00', 'Z'),
        }

        self.save_json(agents_index, self.dist_path / "index.json")
        print(f"✅ index.json ({len(agents_list)} published agents)")

    def build(self):
        """Execute the full build process."""
        print("\n🚀 Starting agent-index build process...\n")

        self.clean_dist()
        self.build_developers()
        self.build_agents()
        self.build_indexes()

        print("\n" + "="*70)
        print("BUILD SUMMARY")
        print("="*70)
        print(f"📊 Developers: {len(self.developers)} succeeded, {self.failed_developers} failed")
        print(f"🤖 Agents:     {len(self.agents)} succeeded, {self.failed_agents} failed")
        print(f"📁 Output:     {self.dist_path}")
        print("="*70 + "\n")

        if self.failed_developers > 0 or self.failed_agents > 0:
            print(f"⚠️  Build completed with warnings: {self.failed_developers + self.failed_agents} items skipped\n")
        else:
            print("🎉 Build completed successfully!\n")


def main():
    """Main build entry point."""
    base_path = Path(__file__).parent.parent
    builder = IndexBuilder(base_path)

    try:
        builder.build()
    except Exception as e:
        print(f"\n❌ Build failed: {e}\n")
        raise


if __name__ == "__main__":
    main()
