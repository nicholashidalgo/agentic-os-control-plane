<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/nicholashidalgo/agentic-os-control-plane/main/assets/nh-logo-dark.svg" width="80">
    <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/nicholashidalgo/agentic-os-control-plane/main/assets/nh-logo-light.svg" width="80">
    <img alt="Nicholas Hidalgo" src="https://raw.githubusercontent.com/nicholashidalgo/agentic-os-control-plane/main/assets/nh-logo-light.svg" width="80">
  </picture>
</p>

<h1 align="center">Governed Workflow Control Plane</h1>

<p align="center"><b>Production-pattern workflow governance framework for approvals, policy controls, auditability, and operational visibility</b></p>

<p align="center">
  <a href="https://github.com/nicholashidalgo/agentic-os-control-plane"><img src="https://img.shields.io/badge/Repository-View_Source-181717?style=for-the-badge&logo=github&logoColor=white" alt="Repository"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-f5c542?style=for-the-badge" alt="License MIT"></a>
  <a href="https://github.com/nicholashidalgo/agentic-os-control-plane"><img src="https://img.shields.io/badge/Tests-59_passing-22c55e?style=for-the-badge" alt="Tests 59 passing"></a>
  <a href="https://github.com/nicholashidalgo/agentic-os-control-plane"><img src="https://img.shields.io/badge/Components-5_controls-2563eb?style=for-the-badge" alt="Components 5 controls"></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Typer-CLI-5A67D8?style=flat" alt="Typer">
  <img src="https://img.shields.io/badge/pytest-59_tests-0A9EDC?style=flat&logo=pytest&logoColor=white" alt="pytest">
  <img src="https://img.shields.io/badge/YAML-configuration-CB171E?style=flat&logo=yaml&logoColor=white" alt="YAML">
  <img src="https://img.shields.io/badge/Cloudflare_Pages-landing_preview-F38020?style=flat&logo=cloudflarepages&logoColor=white" alt="Cloudflare Pages">
</p>

---

<table>
  <tr>
    <td>
      <p>This repository implements a local-first governed workflow control plane that separates operator intent from execution. It provides policy evaluation, approval routing, controlled execution, audit logging, bounded output paths, skill registration, and a packaged Typer CLI through <code>agentic-os</code>.</p>
      <p>The governance model keeps work inspectable through append-only JSONL audit records, approval ledgers, documented skill contracts, and explicit access boundaries. The repository is intentionally company-neutral and platform-neutral, focused on durable workflow governance rather than provider branding.</p>
    </td>
  </tr>
</table>

## Architecture

```text
┌──────────────────────┐
│   Operator Intent    │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│    agentic-os CLI    │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│    Skill Registry    │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│    Policy Engine     │
└──────┬───────┬───────┘
       │       │
       │       └─────────────────────┐
       ▼                             ▼
┌──────────────┐              ┌──────────────┐
│    ALLOW     │              │     DENY     │
└──────┬───────┘              └──────┬───────┘
       │                             │
       ▼                             ▼
┌──────────────┐              ┌──────────────┐
│  Controlled  │              │   Blocked    │
│  Execution   │              │   Action     │
└──────┬───────┘              └──────────────┘
       │
       ▼
┌──────────────────────┐
│ REQUIRE_APPROVAL     │
│ Approval Ledger      │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Output Boundary Check│
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Append-only Audit Log│
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ Operational Review   │
└──────────────────────┘
```

## Governance Controls

| Control | Artifact | Governance Purpose |
| --- | --- | --- |
| Policy engine | [`src/agentic_os/control_plane/policy.py`](src/agentic_os/control_plane/policy.py) | Classifies actions before execution |
| Approval routing | [`src/agentic_os/control_plane/approvals.py`](src/agentic_os/control_plane/approvals.py) | Routes high-risk actions through durable approval records |
| Audit logging | [`src/agentic_os/control_plane/audit_log.py`](src/agentic_os/control_plane/audit_log.py) | Records execution and approval events |
| Output boundaries | [`src/agentic_os/control_plane/runner.py`](src/agentic_os/control_plane/runner.py) | Restricts writes to governed paths |
| Skill registry | [`src/agentic_os/control_plane/registry.py`](src/agentic_os/control_plane/registry.py) | Keeps executable capabilities inspectable |
| CLI surface | [`src/agentic_os/cli.py`](src/agentic_os/cli.py) | Provides the supported operator interface |

## Pipeline Components

<p>
  <img src="https://img.shields.io/badge/Intake-CLI-3776AB?style=flat-square" alt="Intake CLI">
  <img src="https://img.shields.io/badge/Policy-ALLOW_APPROVAL_DENY-b45309?style=flat-square" alt="Policy ALLOW APPROVAL DENY">
  <img src="https://img.shields.io/badge/Approve-JSONL_LEDGER-d29922?style=flat-square" alt="Approve JSONL LEDGER">
  <img src="https://img.shields.io/badge/Execute-SKILLS-3fb950?style=flat-square" alt="Execute SKILLS">
  <img src="https://img.shields.io/badge/Audit-RUNS_JSONL-7c3aed?style=flat-square" alt="Audit RUNS JSONL">
  <img src="https://img.shields.io/badge/Govern-BOUNDED_WRITES-f85149?style=flat-square" alt="Govern BOUNDED WRITES">
</p>

## Runtime Surface

The maintained runtime surface is the packaged implementation under [`src/agentic_os/`](src/agentic_os/). The supported operator interface is the package and CLI, rather than ad hoc wrapper commands.

The packaged surface provides the control points that matter for governed operation:

- skill discovery through the CLI
- routed execution through the runner
- policy classification before write acceptance
- approval handling through the local approval ledger
- bounded path validation before outputs are accepted

Supported command examples:

```bash
agentic-os list
agentic-os run morning_brief
agentic-os approvals list --status pending
agentic-os approvals approve <approval_id>
```

## Skill Surface

| Skill | Purpose |
| --- | --- |
| `morning_brief` | Creates a dated briefing from recent daily artifacts |
| `vault_cleanup` | Promotes structured raw notes into curated reference material |
| `research_digest` | Converts an input note into a structured digest in the wiki tier |
| `continuation_brief` | Creates a handoff document for the next working session |
| `policy_simulator` | Evaluates proposed actions against active policy without executing them |

## Quick Start

```bash
# 1. Clone
git clone https://github.com/nicholashidalgo/agentic-os-control-plane.git
cd agentic-os-control-plane

# 2. Install
chmod +x install.sh
./install.sh

# 3. List registered skills
agentic-os list

# 4. Run a governed skill
agentic-os run morning_brief

# 5. Inspect pending approvals
agentic-os approvals list --status pending
```

## Tech Stack

| Layer | Implementation |
| --- | --- |
| Runtime | Python 3.12+ |
| CLI | Typer |
| Configuration | YAML |
| Tests | pytest, 59 tests |
| Landing page | Cloudflare Pages |
| Audit storage | Local JSONL artifacts |

## Tests

```bash
python -m pytest -q
```

59 tests cover policy decisions, approval lifecycle, configuration loading, registry behavior, skill execution, path boundaries, and policy simulator behavior.

## Project Structure

```text
agentic-os-control-plane/
├── src/agentic_os/
│   ├── cli.py
│   └── control_plane/
├── skills/
├── docs/
├── landing/
├── tests/
├── data/
├── vault/
├── install.sh
├── pyproject.toml
└── README.md
```

## Known Limitations

- External tool adapters are planned, not included in the current runtime surface.
- Approval and run ledgers are local JSONL artifacts, not a hosted database.
- The landing page is a static operational narrative, not a live control dashboard.
- Runtime behavior is limited to the implemented package surface under `src/agentic_os/`.

<p align="center">
  <a href="https://linkedin.com/in/nicholashidalgo"><img src="https://img.shields.io/badge/LinkedIn-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white" alt="LinkedIn"></a>&nbsp;
  <a href="https://nicholashidalgo.com"><img src="https://img.shields.io/badge/Website-000000?style=for-the-badge&logo=About.me&logoColor=white" alt="Website"></a>&nbsp;
  <a href="mailto:analytics@nicholashidalgo.com"><img src="https://img.shields.io/badge/Email-D14836?style=for-the-badge&logo=gmail&logoColor=white" alt="Email"></a>
</p>
