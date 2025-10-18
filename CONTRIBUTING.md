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
# Create agents directory
mkdir -p developers/your-github-username/agents

# Copy the example agent
cp developers/ironbirdlabs/agents/demo-agent.yaml \
   developers/your-github-username/agents/my-agent.yaml

# Edit the file with your agent metadata
# Required fields: developer, name, version, description, model_dependencies
```

**Important**: The `developer` field must match your folder name to pass validation.

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

### Version Updates

To publish a new version of your agent:

1. Update the `version` field in your agent YAML file (use semantic versioning)
2. Update the `last_updated` timestamp
3. Submit a PR with your changes

The build process is configured to create both version-specific and "latest" endpoints.

### Metadata Changes

You can update any field in your agent metadata or developer profile at any time. Changes take effect when your PR is merged.

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

See `developers/ironbirdlabs/agents/demo-agent.yaml` for a comprehensive example.

**Required fields:**
- `developer` - Must match your folder name
- `name` - Agent name (lowercase, alphanumeric, hyphens only)
- `version` - Semantic version (e.g., 1.0.0)
- `description` - What the agent does
- `model_dependencies` - Array of required AI models

**Recommended fields:**
- `listing_status` - published, unlisted, or archived
- `readiness_level` - experimental, beta, production, or deprecated
- `context` - code, data, general, etc.
- `primary_function` - analysis, generation, transformation, etc.
- `image_repository_url` - Docker image URL
- `source_repository_url` - Source code URL

**Optional enrichment fields:**
- `facets` - Categorization metadata (domains, industries, modalities, etc.)
- `input_schema` - Configurable parameters
- `input_types` / `output_types` - Data type support
- `required_integrations` - External services needed
- `required_egress` - Network access requirements
- `tags` - Searchable keywords
- `capabilities` - Feature descriptions

## Validation Rules

Submissions are checked for the following requirements:

1. **YAML syntax** - Files must be valid YAML
2. **Schema compliance** - Fields must match the JSON schemas
3. **Name matching** - Folder name must match `developer` field in profile.yaml
4. **Developer field** - Agent `developer` must match folder name
5. **Semantic versioning** - Versions must follow `major.minor.patch` format
6. **Required fields** - All required fields must be present

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
