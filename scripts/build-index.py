#!/usr/bin/env python3
"""
Build script for agent-index repository.

This script processes YAML files from the developers/ directory and generates
a structured JSON index that can be served via GitHub Pages.

Output structure:
    dist/
        index.json                          # Main index of all agents
        developers.json                     # List of all developers
        @{developer}/
            profile.json                    # Developer profile
            agents.json                     # List of developer's agents
            {agent}/
                metadata.json               # Agent metadata
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


class IndexBuilder:
    """Builds the agent index from YAML source files."""

    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.developers_path = base_path / "developers"
        self.dist_path = base_path / "dist"
        self.developers: Dict[str, Any] = {}
        self.agents: List[Dict[str, Any]] = []

    def clean_dist(self):
        """Remove and recreate the dist directory."""
        if self.dist_path.exists():
            shutil.rmtree(self.dist_path)
        self.dist_path.mkdir(parents=True)

    def load_yaml(self, yaml_path: Path) -> Dict[str, Any]:
        """Load a YAML file and return parsed data."""
        with open(yaml_path, 'r') as f:
            return yaml.safe_load(f)

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
        agent_file: Path,
        developer_name: str
    ) -> Dict[str, Any]:
        """Process a single agent YAML file."""
        agent_data = self.load_yaml(agent_file)

        # Validate developer field matches folder name
        if agent_data.get('developer') != developer_name:
            raise ValueError(
                f"Agent developer field '{agent_data.get('developer')}' "
                f"does not match folder '{developer_name}'"
            )

        # Add computed fields
        agent_name = agent_data.get('name')
        version = agent_data.get('version')

        agent_data['_id'] = f"{developer_name}/{agent_name}"
        agent_data['_index_name'] = f"@{developer_name}/{agent_name}"

        return agent_data

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
                raise

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

            for agent_file in sorted(agents_dir.glob("*.yaml")):
                try:
                    agent_data = self.process_agent(agent_file, developer_name)
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
                    print(f"❌ {agent_file.name}: {e}")
                    raise

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
            if agent.get('listing_status') != 'published':
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
                'listing_status': agent.get('listing_status'),

                # Repository info (needed for install/view source)
                'image_repository_url': agent.get('image_repository_url'),
                'image_repository_access': agent.get('image_repository_access', 'private'),
                'source_repository_url': agent.get('source_repository_url'),
                'source_repository_access': agent.get('source_repository_access', 'private'),

                # Developer info (for rich cards without extra requests)
                'developer_id': developer_data.get('_id', developer_name),
                'developer_name': developer_data.get('name', developer_name),
                'developer_avatar_url': developer_data.get('avatar_url'),

                # Requirements (shown on cards/modals)
                'model_requirements': agent.get('model_requirements'),
                'required_egress': agent.get('required_egress'),

                # Timestamp
                'created_at': agent.get('created_at', datetime.now(UTC).isoformat().replace('+00:00', 'Z')),

                # IDs
                '_id': agent['_id'],
                '_index_name': agent['_index_name'],
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
        print(f"📊 Developers: {len(self.developers)}")
        print(f"🤖 Agents:     {len(self.agents)}")
        print(f"📁 Output:     {self.dist_path}")
        print("="*70 + "\n")

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
