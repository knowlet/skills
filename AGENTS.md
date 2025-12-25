# AGENTS.md

## Problem Frames Skills

This project contains Agent Skills based on **Problem Frames** methodology for reducing AI hallucinations through hierarchical constraints and specification-driven development.

## Spec Reference

- Agent Skills Specification: https://agentskills.io/specification
- Skills are located in: `skills/` directory

## Available Skills

### Core Skills

| Skill | Trigger | Purpose |
|-------|---------|---------|
| `analyze-frame` | New requirements | Classify problem frame, generate spec directory structure |
| `saga-orchestrator` | Cross-frame flows | Coordinate multiple Sub-agents for Saga/Choreography patterns |
| `cross-context` | Cross-BC dependencies | Design Anti-Corruption Layer for Bounded Context integration |

### Sub-agents

| Skill | Frame Type | Purpose |
|-------|------------|---------|
| `command-sub-agent` | CBF | Command Side design & implementation (Use Case, Aggregate) |
| `query-sub-agent` | IDF | Query Side design & implementation (Read Model, Caching) |
| `reactor-sub-agent` | RIF | Event Handler design (Idempotency, Retry, DLQ) |

### Quality Guards

| Skill | Purpose |
|-------|---------|
| `arch-guard` | Enforce Clean Architecture + DDD + CQRS |
| `coding-standards` | Enforce coding conventions (Java/TypeScript/Go) |
| `enforce-contract` | Validate pre/post-conditions & invariants |
| `generate-acceptance-test` | Generate BDD/ezSpec test skeleton |

## Spec Directory Structure

```
docs/specs/{feature-name}/
├── frame.yaml                 # Problem frame definition
├── requirements/              # Requirements layer (What)
├── machine/                   # Machine layer (How - Application)
├── controlled-domain/         # Domain layer (DDD)
├── cross-context/             # Cross-BC dependencies (ACL)
├── acceptance/                # Acceptance tests
└── runbook/                   # Execution guide
```

## Workflow

### Single Frame
```
Requirements → analyze-frame → Spec Directory → Sub-agent → Quality Guards → Acceptance Tests
```

### Cross-Frame (Saga)
```
Complex Flow → saga-orchestrator → runSubagent → [command|query|reactor] → Quality Guards
```

### Cross-BC Dependencies
```
analyze-frame → identify cross_context_dependencies → cross-context → ACL Design → Sub-agent integration
```

## Sub-agent Integration

This skills collection is designed for Claude Code's `runSubagent` dispatching:

```
saga-orchestrator
    ├── runSubagent → command-sub-agent (CBF tasks)
    ├── runSubagent → query-sub-agent (IDF tasks)
    ├── runSubagent → reactor-sub-agent (RIF tasks)
    └── cross-context → ACL design for each step
```

## Frame Concerns Traceability

Each Frame Concern in `frame.yaml` must have `satisfied_by` links:

```yaml
frame_concerns:
  - id: FC1
    name: "Structure Integrity"
    satisfied_by:
      - controlled-domain/aggregate.yaml#invariants.shared
      - tests#lane-hierarchy
```

## Tooling

### Spec Validator

Use the validator script to check spec completeness:

```bash
python ~/.claude/skills/analyze-frame/scripts/validate_spec.py docs/specs/{feature-name}/
```

### Templates

The `analyze-frame` skill provides YAML templates:

| Template | Purpose |
|----------|---------|
| `frame.yaml` | Problem Frame definition |
| `requirements/req-template.yaml` | Requirement specification |
| `machine/use-case.yaml` | Use Case (CBF) |
| `machine/query.yaml` | Query (IDF) |
| `machine/reactor.yaml` | Reactor (RIF) |
| `controlled-domain/aggregate.yaml` | Aggregate with invariants |
| `acceptance/acceptance.yaml` | BDD test scenarios |
| `cross-context/authorization.yaml` | ACL specification |
| `runbook/execute.md` | Execution guide |

Templates location: `~/.claude/skills/analyze-frame/templates/`

## Multi-language Support

| Language | Reference |
|----------|-----------|
| Java | `coding-standards/SKILL.md` |
| TypeScript | `coding-standards/references/TYPESCRIPT.md` |
| Go | `coding-standards/references/GOLANG.md` |

## Usage in Claude Code

To use these skills, copy them to:
- Personal: `~/.claude/skills/`
- Project: `.claude/skills/`

See [README.md](README.md) for detailed instructions.
