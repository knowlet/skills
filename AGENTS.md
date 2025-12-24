# AGENTS.md

## Problem Frames Skills

This project contains Agent Skills based on **Problem Frames** methodology for reducing AI hallucinations through hierarchical constraints.

## Spec Reference

- Agent Skills Specification: https://agentskills.io/specification
- Skills are located in: `skills/` directory

## Available Skills

| Skill | Trigger | Purpose |
|-------|---------|---------|
| `analyze-frame` | New requirements | Classify problem frame (CBF/IDF/RIF), generate YAML spec |
| `saga-orchestrator` | Cross-frame flows | Coordinate multiple Sub-agents for Saga/Choreography patterns |
| `arch-guard` | Code changes | Enforce Clean Architecture + DDD + CQRS |
| `coding-standards` | Implementation | Enforce coding conventions (Java/TypeScript/Go) |
| `command-sub-agent` | frame_type=CBF | Command Side design & implementation |
| `query-sub-agent` | frame_type=IDF | Query Side design & implementation |
| `reactor-sub-agent` | frame_type=RIF | Event reaction & integration |
| `enforce-contract` | Testing/Commit | Validate pre/post-conditions & invariants |
| `generate-acceptance-test` | After spec | Generate BDD/ezSpec test skeleton |

## Workflow

### Single Frame
```
Requirements → analyze-frame → [CBF/IDF/RIF] → sub-agent → Quality Guards → Acceptance Tests
```

### Cross-Frame (Saga)
```
Complex Flow → saga-orchestrator → runSubagent → [command|query|reactor] → Quality Guards
```

## Sub-agent Integration

This skills collection is designed for Claude Code's `runSubagent` dispatching:

```
saga-orchestrator
    ├── runSubagent → command-sub-agent (CBF tasks)
    ├── runSubagent → query-sub-agent (IDF tasks)
    └── runSubagent → reactor-sub-agent (RIF tasks)
```

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
