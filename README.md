# agent-index

An open-source, Git-based index for AI agents enabling federated discovery. Developers manage their own agent metadata through pull requests, and the index is automatically built and published via GitHub Pages.

## Overview

The agent-index repository provides a transparent, community-driven way to publish and discover AI agents. Instead of a centralized API, developers maintain their agent metadata in YAML files within their own folders, with folder ownership checked via GitHub fork ownership.

**Disclaimer**: This index provides metadata submitted by developers. Inclusion in this index does not constitute endorsement, verification, or any guarantee regarding agent quality, functionality, security, or reliability. Users should evaluate agents independently before use.

## Features

- **Open publishing**: No gatekeepers for agent metadata—automated validation only
- **Developer-owned**: Each developer manages their own folder via fork ownership
- **Git-based**: Full version control and auditability for all agent metadata
- **Automated validation**: GitHub Actions validates all changes—no manual approval needed
- **Auto-merge**: PRs that pass validation are automatically merged
- **Federated**: Anyone can fork and run their own index—multiple indexes can coexist
- **Static JSON API**: Served via GitHub Pages for high availability
- **Zero configuration**: No accounts, API keys, or approval processes

## Repository Structure

```
agent-index/
├── developers/              # Developer folders
│   └── {github-username}/   # One folder per developer
│       ├── profile.yaml     # Developer profile
│       └── agents/          # Agent definitions
│           └── {agent-name}/
│               ├── agent.yaml       # Agent identity
│               ├── versions.yaml    # Version management
│               └── {version}.yaml   # Version specifications (0.1.0.yaml, etc.)
├── schema/                  # JSON schemas for validation
│   ├── developer.schema.json
│   ├── agent-identity.schema.json
│   ├── versions.schema.json
│   └── agent-version.schema.json
├── scripts/                 # Build and validation scripts
│   ├── validate.py
│   └── build-index.py
└── dist/                    # Generated JSON (published to GitHub Pages)
    ├── index.json           # All published agents
    ├── developers.json      # All developers
    └── @{developer}/        # Scoped by developer
        ├── profile.json
        ├── agents.json
        └── {agent}/
            └── metadata.json
```

## Getting Started

### Quick Start: Publishing Your First Agent

1. **Fork this repository** to your GitHub account
2. **Clone your fork** locally
3. **Create your developer folder**: `developers/your-github-username/`
4. **Copy and edit** `profile.yaml` from the examples folder
5. **Copy and edit** `agents/demo-agent.yaml` from the examples folder
6. **Submit a pull request** - it should auto-merge if validation passes!

**📚 Full documentation**: [List on Index](https://docs.agentsystems.ai/deploy-agents/list-on-index)

### Quick Reference

**Repository Structure**:
```
developers/your-username/
├── profile.yaml          # Your developer profile
└── agents/
    └── your-agent.yaml   # Your agent metadata
```

**What happens when you submit a PR**:
- ✅ YAML validation runs automatically
- ✅ Folder ownership is checked (must match your GitHub username)
- ✅ PR auto-merges if all checks pass
- ✅ Index updates should reflect shortly after merge

**Need help?** See our [complete guide](https://docs.agentsystems.ai/deploy-agents/list-on-index) with full schema documentation.

### For Consumers: Using the Index

The index is available as static JSON at:

```
https://agentsystems.github.io/agent-index/
```

**Endpoints:**

- `/index.json` - All published agents
- `/developers.json` - All developers
- `/@{developer}/profile.json` - Developer profile
- `/@{developer}/agents.json` - Developer's agents
- `/@{developer}/{agent}/metadata.json` - Latest agent metadata
- `/@{developer}/{agent}/{version}/metadata.json` - Version-specific metadata

**Example:**

```javascript
// Fetch all agents
const response = await fetch('https://agentsystems.github.io/agent-index/index.json');
const { agents } = await response.json();

// Fetch specific agent metadata
const agentMeta = await fetch(
  'https://agentsystems.github.io/agent-index/@ironbirdlabs/document-processor/metadata.json'
);
const metadata = await agentMeta.json();
```

## Schemas

All YAML files are validated against JSON schemas:

- **Developer Profile**: `schema/developer.schema.json`
- **Agent Identity**: `schema/agent-identity.schema.json`
- **Version Management**: `schema/versions.schema.json`
- **Version Specification**: `schema/agent-version.schema.json`

See the example files in `examples/agents/demo-agent/` for comprehensive documentation of all available fields.

## Validation

The validation script checks the following requirements:

1. YAML syntax must be valid
2. All required fields must be present
3. Field values must match schema constraints
4. Folder names must match `developer` fields in profile.yaml
5. Agent `developer` fields must match folder names

Note: Validation checks file structure and required fields but does not verify agent functionality, quality, or security.

Validation is configured to run automatically on every pull request.

## Build Process

When changes are merged to main:

1. Validation checks file structure and schema compliance
2. Build script processes YAML files into JSON
3. JSON files are deployed to GitHub Pages
4. Index should propagate to CDN shortly after deployment

---

## Architecture & Implementation

### Overview

This repository implements a **fully automated, federated agent registry** using GitHub's native features. The system is designed to accept contributions from external developers with zero manual approval while applying different policies to core infrastructure files.

This serves as the **reference implementation** and default index for AgentSystems. Anyone can fork this repository to run their own independent index, enabling a federated discovery model where multiple indexes can coexist.

### Key Design Principles

1. **Path-based security**: Different policies for `developers/**` (open) vs core files (protected)
2. **Fork-based ownership**: Folder ownership checked via GitHub fork ownership
3. **Automated validation**: All checks run programmatically, no human gatekeepers
4. **Defense in depth**: Multiple layers of validation (Policy Gate + CODEOWNERS + required checks)

---

### Workflow Architecture

The system uses three main GitHub Actions workflows:

#### 1. **Policy Gate** (`.github/workflows/policy-gate.yml`)

**Trigger**: `pull_request` (all PRs to main)

**Purpose**: Path-aware enforcement - different rules for core vs developers folders

**Logic**:
- **For `developers/**` only PRs**:
  - ✅ Validates exactly one developer folder is modified
  - ✅ Validates folder name matches fork owner (GitHub account)
  - ✅ Warns if PR author is in CODEOWNERS (neutrality check)
  - ✅ **Passes immediately** (fast path)

- **For core file PRs** (`.github/`, `schema/`, `scripts/`, etc.):
  - ✅ Requires fresh approval from maintainer on latest commit
  - ✅ Blocks self-approval (approver ≠ PR author)
  - ✅ Blocks last-pusher approval (approver ≠ last commit author)
  - ✅ Requires signed commits
  - ✅ Maintainer list pulled from CODEOWNERS file
  - ❌ **Fails** until all conditions met

**Security**: Runs on PR head (safe for public contributions)

#### 2. **Auto-Merge** (`.github/workflows/auto-merge.yml`)

**Trigger**: `pull_request_target` on `developers/**` paths

**Purpose**: Automatically approve and merge developer PRs that pass validation

**Logic**:
1. Validates PR only touches `developers/` folder
2. Validates single developer folder modified
3. Validates folder matches fork owner
4. Auto-approves PR with GitHub App token
5. Enables auto-merge (`gh pr merge --auto --squash`)
6. GitHub merges automatically once all required checks pass

**Security**:
- Uses `pull_request_target` (workflow code from main, not PR)
- Checks out main branch only (never executes PR code)
- All validation via GitHub API

#### 3. **Build and Deploy** (`.github/workflows/build-and-deploy.yml`)

**Trigger**: `pull_request` + `push` to main

**Purpose**: Validate YAML, build JSON index, deploy to GitHub Pages

**Steps**:
- **For PRs**: Validates only changed developer folders (scoped validation)
- **For push to main**: Validates all YAML files against schemas
- Builds `index.json` and `developers.json`
- Deploys to GitHub Pages (on push to main only)

---

### Branch Protection

**Ruleset**: "Main Branch Protection (agent-index) - Updated"

**Configuration**:
```json
{
  "required_approving_review_count": 0,
  "require_code_owner_review": true,
  "require_last_push_approval": false,
  "dismiss_stale_reviews_on_push": true,
  "required_status_checks": [
    "Enforce core vs developers policy",
    "Validate YAML Files",
    "Build JSON Index",
    "Deploy to GitHub Pages"
  ]
}
```

**Why 0 approvals?**: Policy Gate programmatically enforces approval requirements for core files only. Setting general approval requirement would block auto-merge for developers.

**CODEOWNERS**: Protects core files (`.github/`, `schema/`, `scripts/`, README, etc.) by requiring maintainer approval. Provides defense-in-depth with Policy Gate.

---

### GitHub App Setup

**Required Permissions**:
- **Pull requests**: Read and write (approve PRs, enable auto-merge)
- **Contents**: Read and write (merge PRs)
- **Metadata**: Read-only (auto-enabled)

**Secrets** (configured in repository settings):
- `APP_ID`: GitHub App ID
- `APP_PRIVATE_KEY`: GitHub App private key (PEM format)

**Repository Settings**:
- ✅ Allow auto-merge (Settings → General → Pull Requests)
- ✅ GitHub Actions: "Allow all actions and reusable workflows"
- ✅ Workflow permissions: Read and write

---

### Security Model

#### Fork-Based Ownership

Instead of a manual "claim namespace" process, ownership is checked through **GitHub fork ownership**:

1. Developer forks `agentsystems/agent-index`
2. Developer creates `developers/their-username/` folder
3. Developer submits PR from their fork
4. Policy Gate checks: `github.event.pull_request.head.repo.owner.login == folder_name`
5. If match → developer owns that folder ✅

**Why this works**: GitHub enforces fork ownership - developers can only push to their own forks. This creates GitHub-authenticated ownership verification tied to GitHub accounts.

#### Defense in Depth

Multiple validation layers are configured:

1. **Policy Gate**: Validates folder ownership + scope
2. **CODEOWNERS**: Requires maintainer approval for core files
3. **Schema validation**: Catches malformed YAML
4. **Required checks**: All must pass before merge
5. **Branch protection**: Prevents force push, requires linear history
6. **Auto-merge queuing**: Merge only happens after all checks green

#### Why `pull_request_target`?

Auto-merge uses `pull_request_target` instead of `pull_request` or `workflow_run`:

- ✅ **Runs for fork PRs** (unlike `workflow_run`)
- ✅ **Has write permissions** (can approve/merge)
- ✅ **Runs workflow from main** (attacker can't modify auto-merge logic)
- ✅ **Has access to secrets** (GitHub App token)

**Critical safety**: Workflow checks out main branch only, never PR code. All validation uses GitHub API (`gh pr view`).

---

### Troubleshooting

#### Auto-merge not triggering

**Symptom**: PR passes all checks but auto-merge workflow doesn't run

**Causes**:
1. **Repository setting disabled**: Settings → General → Pull Requests → ☑️ "Allow auto-merge"
2. **GitHub App lacks permissions**: App needs "Contents: Write" permission
3. **PR doesn't touch `developers/**`**: Auto-merge only triggers on `paths: ['developers/**']`

#### Policy Gate false negatives

**Symptom**: Policy Gate passes when it shouldn't (security issue!)

**Check**:
1. Workflow has checkout step (needed for `gh pr view` to work)
2. Changed files list is populated (`steps.files.outputs.changed` not empty)
3. Regex pattern matches correctly (`^developers/` for developers folder)

#### Required checks not running

**Symptom**: PR shows "Expected — Waiting for status to be reported"

**Causes**:
1. **Context name mismatch**: Ruleset requires exact job name match
   - ✅ Correct: `"Enforce core vs developers policy"` (job name)
   - ❌ Wrong: `"Policy Gate / gate"` (workflow / job)
2. **Workflow not on main**: Workflows must exist on main branch to run as required checks
3. **First-time contributor**: Org settings may require manual approval (Settings → Actions → General)

#### GitHub App permission errors

**Symptom**: `GraphQL: Resource not accessible by integration`

**Solution**: Update GitHub App permissions:
1. Go to `https://github.com/organizations/agentsystems/settings/apps/[app-name]`
2. Update repository permissions
3. Click "Save changes"
4. Accept new permissions on repositories where app is installed

---

### Recreating This Setup

If you need to rebuild this system from scratch:

1. **Create repository**:
   - Standard structure with `developers/` folder containing only `.gitkeep`
   - Do not include any example developer folders (keeps git history clean)

2. **Update CODEOWNERS**: Add your maintainer GitHub usernames (workflows read from this file)

3. **Push initial code**:
   - Add all files (workflows, schemas, scripts, examples, docs)
   - Do not include any folders under `developers/` except `.gitkeep`

4. **Create GitHub App**:
   - Settings → Developer settings → GitHub Apps → New
   - Permissions: Pull requests (RW), Contents (RW), Metadata (R)
   - After creation, click "Install App" and select your repository
   - Note: Must explicitly grant repository access after app creation

5. **Add secrets**: `APP_ID` and `APP_PRIVATE_KEY`

6. **Configure branch protection**:
   - Create ruleset targeting main branch
   - Set `required_approving_review_count: 0`
   - Add required checks (exact job names from workflows)
   - Enable `require_code_owner_review: true`
   - Tip: Rulesets can be exported as JSON and imported to other repositories

7. **Enable GitHub Pages**: Settings → Pages → Source: GitHub Actions

8. **Enable auto-merge**: Settings → General → Pull Requests → ☑️ Allow auto-merge

9. **Bootstrap workflows**:
   - First commit to main requires admin bypass (workflows don't exist yet to run as checks)
   - After workflows are on main, system operates autonomously

---

## Running Your Own Index

This repository is designed to be forked and run independently. Organizations, communities, or regions may want to run their own agent indexes for various reasons:

- **Private/Enterprise**: Internal agent discovery for your organization
- **Community-Specific**: Curated indexes for specific domains (healthcare, finance, research, etc.)
- **Regional**: Localized indexes with regional compliance requirements
- **Testing/Development**: Sandbox environments for testing before publishing to public indexes

### Quick Fork Setup

1. **Fork this repository** to your organization
2. **Update `CODEOWNERS`** with your maintainer team (required - workflows read from this file)
3. **Follow "Recreating This Setup"** above to configure workflows and permissions
4. **Customize** (optional):
   - Modify validation rules in `scripts/validate.py`
   - Adjust schemas in `schema/` if needed
   - Customize branch protection rules
5. **Enable GitHub Pages** - your index will be at `https://your-org.github.io/agent-index/`
6. **Invite developers** to fork and submit PRs

### Maintenance Considerations

**Regular Tasks**:
- Monitor workflow runs for failures
- Review and update required status checks as workflows evolve
- Keep schemas up-to-date with agent platform changes
- Respond to issues/discussions from developers

**Security**:
- Regularly audit Policy Gate logic for bypass opportunities
- Review GitHub App permissions and rotate keys periodically
- Monitor for suspicious PRs (unusual patterns, spam, etc.)
- Keep dependencies in workflows updated

**Customization**:
- Modify approval requirements in Policy Gate for your organization's needs
- Add custom validation rules (e.g., require specific fields, enforce naming conventions)
- Implement additional required checks (security scans, license validation, etc.)

### Differences from Public Index

When running your own index:

- ✅ **Full control**: Set your own policies and requirements
- ✅ **Privacy**: Keep agent metadata private if needed (disable GitHub Pages, use private repo)
- ✅ **Customization**: Modify schemas and validation for your use case
- ⚠️ **Maintenance**: Responsible for updates, security, and availability
- ⚠️ **Discovery**: Developers must know about your index to publish to it

---

## Federation & Multiple Indexes

The AgentSystems platform supports **connecting to multiple agent indexes** simultaneously. This enables a federated discovery model where different indexes can coexist:

### Index Connections in AgentSystems UI

Users can configure multiple index connections in the AgentSystems UI:

1. **Public Index** (default): `https://agentsystems.github.io/agent-index/`
2. **Private/Organizational Indexes**: Your company's internal index
3. **Community Indexes**: Domain-specific curated indexes
4. **Regional Indexes**: Indexes hosted in specific regions for compliance

The UI aggregates agents from all configured indexes for unified discovery.

### Why Multiple Indexes?

**Federation Model**:
- Anyone can fork and run their own index—no permission required
- Forkable infrastructure reduces barriers to entry
- Multiple independent indexes can coexist
- Community-driven curation across different contexts

**Flexibility**:
- Organizations can maintain internal indexes with custom policies
- Communities can create specialized indexes for specific domains
- Geographic distribution enables regional compliance and lower latency

**User Choice**:
- Users choose which indexes to connect to and consume
- Different indexes can have different validation policies
- All metadata is auditable via Git history
- Reputation emerges organically through usage and community feedback

### Publishing to Multiple Indexes

Developers can publish their agents to multiple indexes:

1. Fork each index repository
2. Submit PRs to each (same YAML files work across indexes)
3. Agents appear in all indexes where PRs are merged

**Note**: Each index may have different policies and approval requirements.

### Creating a Discoverable Index

To make your index discoverable by AgentSystems users:

1. **Deploy to GitHub Pages** (or any static host)
2. **Follow the schema** - ensure your index produces `index.json` and `developers.json` in the expected format
3. **Announce your index** - share the base URL (e.g., `https://your-org.github.io/agent-index/`)
4. **Document your policies** - help developers understand your requirements

Users can then add your index URL in their AgentSystems UI configuration.

### Index Compatibility

Indexes should:
- ✅ Serve JSON at `/index.json` (all agents) and `/developers.json` (all developers)
- ✅ Follow the schema structure (see "For Consumers: Using the Index" above)
- ✅ Serve over HTTPS
- ✅ Include proper CORS headers if consumed by web clients
- ⚠️ Document any custom fields or extensions

The AgentSystems UI is designed to be resilient to index differences and should skip agents with invalid/incomplete metadata.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines on:

- Adding your developer profile
- Publishing agents
- Updating existing agents
- Schema field descriptions
- Best practices

## License

Apache-2.0 License - see [LICENSE](LICENSE) for details.

## Support

- **Issues**: https://github.com/agentsystems/agent-index/issues
- **Discussions**: https://github.com/agentsystems/agent-index/discussions
- **Documentation**: https://docs.agentsystems.ai

---

https://agentsystems.ai