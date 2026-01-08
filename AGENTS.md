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
| `coding-standards` | Enforce coding conventions (Java/TypeScript/Go/Rust) |
| `enforce-contract` | Validate pre/post-conditions & invariants |
| `generate-acceptance-test` | Generate BDD/ezSpec test skeleton |

### Review & Validation

| Skill | Purpose |
|-------|---------|
| `code-reviewer` | Automated code review (architecture, standards, spec compliance) |
| `spec-compliance-validator` | Validate spec completeness & format compliance |
| `multi-model-reviewer` | Multi-AI verification (Spec == Program == Test) |

## Spec Directory Structure

```
docs/specs/{feature-name}/
├── frame.yaml                 # Problem frame definition
├── acceptance.yaml            # Acceptance criteria (at root)
├── requirements/              # Requirements layer (What)
│   └── cbf-req-1-{feature}.yaml
├── machine/                   # Machine layer (How - Application)
│   ├── machine.yaml
│   ├── controller.yaml
│   └── use-case.yaml
├── controlled-domain/         # Domain layer (DDD)
├── cross-context/             # Cross-BC dependencies (ACL)
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

### Test Generator

Use the test generator to create BDD test skeletons:

```bash
# Generate Gherkin .feature file
python ~/.claude/skills/generate-acceptance-test/scripts/generate_tests.py \
    docs/specs/{feature-name}/ --lang gherkin

# Generate language-specific tests
python ~/.claude/skills/generate-acceptance-test/scripts/generate_tests.py \
    docs/specs/{feature-name}/ --lang typescript --output tests/acceptance/
```

Supported languages: `gherkin`, `typescript`, `go`, `rust`

### Multi-Model Review

Use multi-model review for comprehensive verification:

```bash
# Full review (Spec == Program == Test)
python ~/.claude/skills/multi-model-reviewer/scripts/multi_model_review.py \
    --spec-dir docs/specs/{feature-name}/ \
    --program-dir src/{aggregate}/ \
    --test-dir tests/{aggregate}/ \
    --output review-report.yaml

# Use specific models
python ~/.claude/skills/multi-model-reviewer/scripts/multi_model_review.py \
    --spec-dir docs/specs/{feature-name}/ \
    --program-dir src/ --test-dir tests/ \
    --models chatgpt,claude,gemini
```

**Supported Models:**
| Model | Method | Role |
|-------|--------|------|
| ChatGPT 5.2 | OpenAI API | Semantic analysis |
| Gemini | Local CLI | Multi-modal review |
| Codex | Local CLI | Code understanding |
| QWEN 32B | Ollama | Fast local inference |
| Claude | Local CLI | Final arbiter (false positive filter) |

### Templates

The `analyze-frame` skill provides YAML templates:

| Template | Purpose |
|----------|---------|
| `frame.yaml` | Problem Frame definition |
| `acceptance.yaml` | Acceptance criteria (Gherkin-like, ezSpec compatible) |
| `requirements/req-template.yaml` | Requirement specification |
| `machine/machine.yaml` | Machine definition |
| `machine/controller.yaml` | API Controller specification |
| `machine/use-case.yaml` | Use Case (CBF) |
| `machine/query.yaml` | Query (IDF) |
| `machine/reactor.yaml` | Reactor (RIF) |
| `controlled-domain/aggregate.yaml` | Aggregate with invariants |
| `cross-context/authorization.yaml` | ACL specification |
| `runbook/execute.md` | Execution guide |

Templates location: `~/.claude/skills/analyze-frame/templates/`

## Multi-language Support

| Language | Reference |
|----------|-----------|
| Java | `coding-standards/SKILL.md` |
| TypeScript | `coding-standards/references/TYPESCRIPT.md` |
| Go | `coding-standards/references/GOLANG.md` |
| Rust | `coding-standards/references/RUST.md` |

### BDD Frameworks

| Language | Framework | Step Definition |
|----------|-----------|-----------------|
| Java | ezSpec | Auto-generated (Fluent API) |
| Go | Ginkgo + Gomega | Built-in BDD style |
| TypeScript | Cucumber.js / Jest-Cucumber | Manual / Auto |
| Rust | cucumber-rs | Macro-assisted |

## Usage in Claude Code

To use these skills, copy them to:
- Personal: `~/.claude/skills/`
- Project: `.claude/skills/`

See [README.md](README.md) for detailed instructions.
