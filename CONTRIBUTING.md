# Contributing to Agent Index

Thank you for your interest in contributing to AgentSystems! This project consists of multiple repositories working together to provide a complete AI agent platform.

**Important**: By submitting agent metadata to this index, you represent that you have the right to publish the information and that the metadata accurately describes your agent. Inclusion in this index does not constitute endorsement or verification by AgentSystems.

## Repository Structure

AgentSystems is organized into several focused repositories:

- **[agentsystems](https://github.com/agentsystems/agentsystems)** - Main documentation and platform overview
- **[agent-control-plane](https://github.com/agentsystems/agent-control-plane)** - Gateway and orchestration services
- **[agentsystems-sdk](https://github.com/agentsystems/agentsystems-sdk)** - CLI and deployment tools
- **[agentsystems-ui](https://github.com/agentsystems/agentsystems-ui)** - Web interface
- **[agentsystems-toolkit](https://github.com/agentsystems/agentsystems-toolkit)** - Development libraries
- **[agent-template](https://github.com/agentsystems/agent-template)** - Reference implementation
- **[agent-index](https://github.com/agentsystems/agent-index)** - Decentralized agent metadata index (this repo)

## Getting Started

### Prerequisites

- GitHub account with commit signing enabled ([Setup Guide](https://docs.github.com/en/authentication/managing-commit-signature-verification))
- Familiarity with YAML

**Security Requirement**: All commits must be signed with a verified GPG or SSH key. Unverified commits will be rejected by the auto-merge workflow.

### Publishing Your First Agent

The agent-index is a Git-based registry where you manage your own agent metadata through YAML files.

#### 1. Fork this repository

Click the "Fork" button at the top of this repository.

#### 2. Clone your fork
```bash
git clone https://github.com/YOUR-USERNAME/agent-index.git
cd agent-index
```

#### 3. Create your developer folder
```bash
mkdir -p developers/your-github-username
```

#### 4. Add your developer profile
```bash
# Copy the example profile
cp developers/ironbirdlabs/profile.yaml developers/your-github-username/

# Edit the file with your information
# Required fields: name, developer
# See schema/developer.schema.json for all available fields
```

**Important**: The folder name must match your `developer` field exactly to pass validation.

#### 5. Add your first agent
```bash
# Create your agent directory
mkdir -p developers/your-github-username/agents/my-agent

# Copy example files
cp examples/agents/demo-agent/agent.yaml \
   developers/your-github-username/agents/my-agent/
cp examples/agents/demo-agent/versions.yaml \
   developers/your-github-username/agents/my-agent/
cp examples/agents/demo-agent/0.1.0.yaml \
   developers/your-github-username/agents/my-agent/

# Edit agent.yaml with identity metadata
# Required fields: developer, name, description, container_image

# Edit versions.yaml with version management
# Required fields: latest_version, listed_versions

# Edit 0.1.0.yaml with version specification
# Required fields: version, model_dependencies
```

**Important**:
- The `developer` field in agent.yaml must match your folder name
- The `name` field in agent.yaml must match the agent directory name
- The `latest_version` field in versions.yaml must match an existing {version}.yaml file
- The `listed_versions` in versions.yaml must all match existing {version}.yaml files
- The `version` field in each {version}.yaml must match the filename (e.g., 0.1.0.yaml contains version: "0.1.0")

#### 6. Validate locally (recommended)
```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install pyyaml jsonschema

# Validate your changes
python scripts/validate.py all
```

#### 7. Commit and push
```bash
git add developers/your-github-username/
git commit -m "Add developer profile and my-agent"
git push origin main
```

#### 8. Submit a pull request

Create a PR from your fork to the main repository. The automated workflow is configured to:
- Validate your YAML files against the schemas
- Check that folder names match `developer` fields in profile.yaml
- Check that agent `developer` fields match folder names
- **Auto-merge** if all checks pass and you're only modifying your own folder

**Auto-merge conditions:**
- ✅ Format validation passes (YAML syntax and schema compliance)
- ✅ Changes are only in `developers/your-github-username/`
- ✅ Your GitHub username matches the folder name (checked via fork ownership)
- ✅ No files outside your developer folder are modified

If these conditions are met, your PR should be automatically approved and merged shortly. Your agent should then appear in the index at `https://agentsystems.github.io/agent-index/`.

**Note:** Automated validation only checks file format and required fields, not agent functionality, quality, or security.

## Updating Existing Agents

### Publishing New Versions

To publish a new version of your agent:

1. Create a new version file:
```bash
# Copy current version as template
cp developers/your-github-username/agents/my-agent/0.1.0.yaml \
   developers/your-github-username/agents/my-agent/0.2.0.yaml
```

2. Edit the new version file (`0.2.0.yaml`):
   - Update `version: "0.2.0"` (must match filename)
   - Modify behavioral changes (model, facets, schema, etc.)
   - Add release notes

3. Update `versions.yaml`:
   - Change `latest_version: "0.1.0"` to `latest_version: "0.2.0"`
   - Add `"0.2.0"` to `listed_versions` array
   - Optionally remove old versions from `listed_versions` to hide them

4. Submit a PR with your changes

**Why this structure is better**: Adding 0.2.0 shows as a clean new file in git diff, making PRs simple and reviewable. All version management is centralized in versions.yaml.

### Updating Agent Identity

To update your agent's identity (description, tags, capabilities):

1. Edit `developers/your-github-username/agents/my-agent/agent.yaml`
2. Submit a PR

Note: Identity fields affect all versions. Version-specific changes go in {version}.yaml files.

## Field Reference

### Developer Profile Fields

See `developers/ironbirdlabs/profile.yaml` for a comprehensive example with all available fields and descriptions.

**Required fields:**
- `name` - Display name
- `developer` - Developer namespace, must match folder name

**Recommended fields:**
- `type` - individual, organization, company, or enterprise
- `bio` - Short description
- `website` - Your website URL
- `support_email` - Contact email

### Agent Definition Fields

See `examples/agents/demo-agent/` for a comprehensive example.

**agent.yaml - Agent Identity (Never changes):**

These fields define the agent's identity.

*Required:*
- `developer` - Must match your folder name
- `name` - Agent name (lowercase, alphanumeric, hyphens only)
- `description` - What the agent does
- `container_image` - Container image reference (without tag, e.g., docker.io/user/agent)

*Optional:*
- `source_repository_url` - Source code URL
- `primary_function` - Primary function category (research, create, process, monitor, automate, analyze)
- `tags` - Searchable keywords
- `capabilities` - High-level feature descriptions

**versions.yaml - Version Management:**

Controls which versions are latest and visible.

*Required:*
- `latest_version` - Latest version (must match an existing {version}.yaml file, e.g., "0.1.0")
- `listed_versions` - Array of versions visible in discovery (each must match an existing {version}.yaml file)

**{version}.yaml - Complete Specifications:**

Each version is a complete, self-contained specification. All behavioral characteristics can differ between versions.

*Required in each version file:*
- `version` - Semantic version (e.g., 0.1.0 or 0.1.0-beta.1), used as container image tag
- `model_dependencies` - Array of required AI models

*Optional in each version:*
- `readiness_level` - Maturity level (experimental, beta, production, deprecated)
- `container_image_access` - Access level (public or private)
- `source_repository_access` - Source access level (public or private)
- `input_types` - Supported input data types
- `output_types` - Supported output data types
- `input_schema` - Configurable parameters
- `required_egress` - Network access requirements
- `required_integrations` - External services needed
- `facets` - Behavioral characteristics and categorization:
  - `context` - Operating context (personal, professional, general)
  - `autonomy` - Autonomy level (Assist, Co-pilot, Auto-pilot)
  - `latency` - Latency profile (real-time, interactive, batch)
  - `cost_profile` - Cost model (free, $/task, $/month)
  - `modalities` - Supported modalities (text, image, audio, video)
  - `domains` - Application domains
  - `model_tooling` - Model frameworks (LLM, RAG, fine-tuned, embeddings)
  - `industries` - Target industries
  - `integrations` - Supported integrations
- `release_notes` - Markdown-formatted release notes

## Validation Rules

Submissions are checked for the following requirements:

1. **YAML syntax** - Files must be valid YAML
2. **Schema compliance** - Files must match their respective JSON schemas:
   - `agent.yaml` → `agent-identity.schema.json`
   - `versions.yaml` → `versions.schema.json`
   - `{version}.yaml` → `agent-version.schema.json`
3. **Developer name matching** - Folder name must match `developer` field in profile.yaml
4. **Agent developer field** - Agent `developer` in agent.yaml must match folder name
5. **Agent name matching** - Agent `name` in agent.yaml must match directory name
6. **versions.yaml exists** - Every agent directory must contain versions.yaml
7. **Latest version exists** - `latest_version` field in versions.yaml must point to an existing {version}.yaml file
8. **Listed versions exist** - All versions in `listed_versions` must have corresponding {version}.yaml files
9. **Version filename matching** - Version in {version}.yaml must match filename (e.g., 0.1.0.yaml contains `version: "0.1.0"`)
10. **Semantic versioning** - Versions must follow `x.y.z` or `x.y.z-prerelease` format (e.g., 0.1.0 or 1.0.0-beta.1)
11. **Required fields** - All required fields must be present in agent.yaml, versions.yaml, and version files
12. **Version files exist** - At least one {version}.yaml file must exist

Note: Validation checks file structure and required fields but does not verify agent functionality, quality, or security.

## Code Standards

For infrastructure contributions (scripts, schemas, workflows):

- Follow the existing code style
- Add tests for new functionality
- Update documentation as needed
- Use clear, descriptive commit messages

## Pull Request Process

1. Run validation locally before submitting
2. Provide a clear description of changes
3. Wait for automated validation in PR
4. Address any feedback from reviewers
5. Once approved and merged, changes should typically be live within minutes

## Community Guidelines

Please read our [Code of Conduct](https://github.com/agentsystems/agentsystems/blob/main/CODE_OF_CONDUCT.md) to understand our community standards.

## Questions?

- **General questions**: Open a discussion in the [main repository](https://github.com/agentsystems/agentsystems)
- **Agent index questions**: Create an issue in this repository
- **Validation errors**: Check the schema files in `schema/` or ask in an issue

We appreciate all contributions, from first-time agent publishers to infrastructure improvements!
