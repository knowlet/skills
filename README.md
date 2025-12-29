# Problem Frames Skills

[正體中文](README.zh-hant.md)

Agent Skills designed based on the **Problem Frames** theory, reducing AI hallucinations through a multi-layered constraint architecture, achieving "separation of requirements and implementation" and "specifications as documentation, documentation as specifications."

---

## Table of Contents

- [Quick Start](#quick-start)
- [Design Philosophy](#design-philosophy)
- [Specification Directory Structure](#specification-directory-structure)
- [Skills List](#skills-list)
- [Workflow](#workflow)
- [Usage Examples](#usage-examples)
- [References](#references)

---

## Plugins vs. Skills: Which One to Choose?

This project currently uses a **Hybrid Architecture**, supporting both "Claude Plugin" and "Direct Skills" invocation methods. Here is a comparison and recommendation:

| Feature | Claude Plugin (Recommended) | Direct Skills (Legacy) |
|------|---------------------|------------------------|
| **Invocation** | **Slash Commands** (`/analyze`) or `@AgentName` | **Natural Language** ("Help me analyze...") |
| **Trigger Accuracy** | **High** (Explicit commands, never misidentified) | **Medium** (Relies on semantic matching, can be unstable) |
| **Setup Difficulty** | **Low** (Single command to load directory) | **High** (Requires manual copying of multiple files) |
| **Multi-step Tasks** | **Strong** (Triggers complex scripts via Slash Command) | **Average** (Requires step-by-step prompting) |
| **Scope** | Complex frameworks, team collaboration, fixed flows | Individual trials, flexible exploration |

### Why Use a Plugin?

For a rigorous software engineering framework like **Problem Frames**, we strongly recommend the **Plugin mode** for the following reasons:

1.  **Explicit Intent Start**: Use `/analyze` to explicitly tell Claude "start problem analysis now," avoiding accidental triggers in general conversation.
2.  **Encapsulating Complexity**: Saga Orchestrator involves cooperation between multiple sub-agents. The `/saga` command loads the necessary context and prompts at once, which is more reliable than manual prompting.
3.  **Version Control**: A plugin as a complete unit is easier to update and sync with teams.

---

## Quick Start

### Method 1: Using as a Claude Plugin (Recommended)

No need to copy files, load directly in the project root:

```bash
# Start Claude Code in this directory
claude --plugin-dir .
```

**Development Examples:**

*   **Analyze New Requirement**:
    ```text
    /analyze User wants a "Daily Inventory Report" feature, needs to read data from Warehouse Context and send Email
    ```

*   **Execute Saga Flow**:
    ```text
    /saga Process "User Order" flow, including stock deduction (StockContext) and payment processing (PaymentContext)
    ```

*   **Call Specific Agent**:
    ```text
    @command-sub-agent Please implement createOrder method according to aggregate.yaml
    ```

### Method 2: Using as Personal Skills (Legacy)

Copy skills to the global configuration directory:

```bash
cp -r skills/* ~/.claude/skills/
```

**Development Examples:**

*   **Natural Language Trigger**:
    ```text
    Please help me analyze the Problem Frame structure for "Daily Inventory Report"
    ```

After starting Claude Code, ask:
```
What Skills are available?
```

---

## Design Philosophy

### Multi-layered Constraint Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Requirement Constraint                                         │
│  requirements/*.yaml → Pure business language, no impl details  │
├─────────────────────────────────────────────────────────────────┤
│  Frame Constraint                                                │
│  frame.yaml → Frame Concerns + Cross-Context Dependencies       │
├─────────────────────────────────────────────────────────────────┤
│  Machine Constraint                                              │
│  machine/*.yaml → Use Case / Query / Reactor Specifications    │
├─────────────────────────────────────────────────────────────────┤
│  Controlled Domain Constraint                                    │
│  controlled-domain/*.yaml → Aggregate + Invariants              │
├─────────────────────────────────────────────────────────────────┤
│  Acceptance Constraint                                           │
│  acceptance/*.yaml → BDD Scenarios + validates_concerns          │
└─────────────────────────────────────────────────────────────────┘
                                ↓
               Hallucination Reduction for AI Problem Solving
```

### Problem Frame Types

| Frame | Description | Sub-agent |
|-------|------|-----------|
| **CBF** | Commanded Behavior - Operator issues commands, system changes state | `command-sub-agent` |
| **IDF** | Information Display - User queries information, system returns data | `query-sub-agent` |
| **RIF** | Required Behavior - System reacts to events, asynchronous processing | `reactor-sub-agent` |
| **WPF** | Workpieces - Editing and managing work products | - |
| **TF** | Transformation - Input data is transformed to produce output | - |

---

## Specification Directory Structure

Each feature corresponds to a specification directory:

```
docs/specs/{feature-name}/
├── frame.yaml                 # Problem Frame definition (Core)
│   ├── frame_concerns         # Concerns + satisfied_by traceability
│   └── cross_context_deps     # Cross-BC dependencies
│
├── requirements/              # Requirement Layer (What) - Pure business
│   └── req-1-{feature}.yaml
│
├── machine/                   # Machine Layer (How) - Application Layer
│   ├── machine.yaml           # Machine Definition
│   ├── controller.yaml        # API Entry Specification
│   ├── use-case.yaml          # Use Case Specification (CBF)
│   ├── query.yaml             # Query Specification (IDF)
│   └── reactor.yaml           # Reactor Specification (RIF)
│
├── controlled-domain/         # Domain Layer
│   └── aggregate.yaml         # Aggregate + Invariants
│
├── cross-context/             # Cross-Bounded Context dependency
│   └── {context-name}.yaml    # ACL Definition
│
├── acceptance/                # Acceptance Tests
│   ├── acceptance.yaml        # Test Specification
│   └── generated/             # AI Generated ezSpec
│       └── {feature}.feature
│
└── runbook/
    └── execute.md             # Execution Guide
```

---

## Skills List

### Core Skills

| Skill | Triggering | Description |
|-------|---------|------|
| [`analyze-frame`](skills/analyze-frame/SKILL.md) | New requirement | Analyzes Problem Frames, generates spec structure |
| [`saga-orchestrator`](skills/saga-orchestrator/SKILL.md) | Cross-frame flow| Coordinates multi-sub-agents, handles Saga pattern |
| [`cross-context`](skills/cross-context/SKILL.md) | Cross-BC dependency | Designs Anti-Corruption Layer |

### Sub-agents

| Skill | Frame | Description |
|-------|-------|------|
| [`command-sub-agent`](skills/command-sub-agent/SKILL.md) | CBF | Use Case, Aggregate, Domain Event |
| [`query-sub-agent`](skills/query-sub-agent/SKILL.md) | IDF | Query Handler, Read Model, Cache |
| [`reactor-sub-agent`](skills/reactor-sub-agent/SKILL.md) | RIF | Event Handler, Idempotency, Retry Mechanism |

### Quality Guard

| Skill | Description |
|-------|------|
| [`arch-guard`](skills/arch-guard/SKILL.md) | Ensures Clean Architecture + DDD + CQRS layering |
| [`coding-standards`](skills/coding-standards/SKILL.md) | Enforces coding standards |
| [`enforce-contract`](skills/enforce-contract/SKILL.md) | Validates pre/post-conditions and invariants |
| [`generate-acceptance-test`](skills/generate-acceptance-test/SKILL.md) | Generates BDD/ezSpec test skeletons |
| [`mutation-testing`](skills/mutation-testing/SKILL.md) | Performs Mutation Testing to verify test quality |

### Multi-language Support

| Language | Reference |
|-----|---------|
| Java | [`coding-standards/SKILL.md`](skills/coding-standards/SKILL.md) |
| TypeScript | [`coding-standards/references/TYPESCRIPT.md`](skills/coding-standards/references/TYPESCRIPT.md) |
| Go | [`coding-standards/references/GOLANG.md`](skills/coding-standards/references/GOLANG.md) |

---

## Workflow

### Single Frame Workflow

```
Requirement Input
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│                        analyze-frame                             │
│       Generate Spec Directory (frame.yaml + Layers YAMLs)        │
└───────────────────────────┬─────────────────────────────────────┘
                             │
           ┌─────────────────┼─────────────────┐
           ▼                 ▼                 ▼
    ┌───────────┐     ┌───────────┐     ┌───────────┐
    │  command  │     │   query   │     │  reactor  │
    │ sub-agent │     │ sub-agent │     │ sub-agent │
    │   (CBF)   │     │   (IDF)   │     │   (RIF)   │
    └─────┬─────┘     └─────┬─────┘     └─────┬─────┘
          │                 │                 │
          │   cross-context (If Cross-BC deps) │
          │                 │                 │
          └─────────────────┼─────────────────┘
                             │
           ┌─────────────────┴─────────────────┐
           │           Quality Guard Layer     │
           │  arch-guard │ coding-standards │  │
           │        enforce-contract           │
           └─────────────────┬─────────────────┘
                             │
                             ▼
                 ┌─────────────────────┐
                 │ generate-acceptance │
                 │       -test         │
                 └─────────────────────┘
```

### Frame Concerns Traceability

```yaml
# frame.yaml
frame_concerns:
  - id: FC1
    name: "Structure Integrity"
    description: "SwimLane must be under a Stage"
    satisfied_by:
      - controlled-domain/aggregate.yaml#invariants.shared
      - tests#lane-hierarchy

# Generated code must implement FC1
# Aggregate.validateInvariants() enforces it
```

### Cross-BC Dependency Handling

```
analyze-frame
    │
    ├── Identify cross_context_dependencies
    │       └── XC1: Authorization (AccessControl BC)
    │
    └── cross-context Skill
            │
            ├── Design ACL Spec (cross-context/authorization.yaml)
            │
            └── command-sub-agent
                    └── Integrate AuthorizationService in Use Case
```

---

## Usage Examples

### Example 1: Analyze New Requirement

```
I have a new requirement: "User can create new Workflow and associate it to a specified Board"
Please help me analyze the Problem Frame type and generate a specification directory.
```

→ Claude uses `analyze-frame`, identifies as CBF, outputs full spec directory.

### Example 2: Handling Cross-BC Dependency

```
This requirement needs permission check: "Only Board Member can create Workflow"
Permission management is in AccessControl BC, please design ACL.
```

→ Claude uses `cross-context`, designs Anti-Corruption Layer.

### Example 3: Generate Code

```
Based on docs/specs/create-workflow/ directory,
please generate CreateWorkflowUseCase code in TypeScript.
```

→ Claude uses `command-sub-agent`, reads spec directory to generate code.

### Example 4: Generate Acceptance Test

```
Based on docs/specs/create-workflow/acceptance/acceptance.yaml
please generate ezSpec test file.
```

→ Claude uses `generate-acceptance-test`, generates .feature and test skeleton.

### Example 5: Regenerate Code

```
Specifications updated, please delete old code and regenerate:
- Delete src/application/use-cases/CreateWorkflow*
- Delete src/domain/aggregates/Workflow*
- Regenerate based on updated specs
```

→ Claude re-reads the spec directory and generates updated code.

---

## How Skills Work

Skills are an open format that allows Agents to dynamically load expertise and capabilities.

### Progressive Disclosure

| Stage | Description | Token Consumption |
|------|------|-----------|
| **Discovery** | Load `name` + `description` at startup | ~100/skill |
| **Activation** | Load full `SKILL.md` when task matches | < 5000 |
| **Execution** | Load `references/`, `scripts/` on demand | As needed |

### Skill Directory Structure

```
skill-name/
├── SKILL.md          # Required: Instructions + metadata
├── scripts/          # Optional: Executable scripts
├── references/       # Optional: Reference documents
└── assets/           # Optional: Templates, resources
```

---

## Theoretical Validation

This architecture has been deeply compared with Michael Jackson's "Problem Frames" theory, confirming that its design highly conforms to the standard of problem frame analysis:

### 1. Frame Mapping

| Problem Frame | Agent Skill | Description |
| :--- | :--- | :--- |
| **Required Behavior** | `reactor-sub-agent` (RIF) | Corresponds to system reaction to domain events (Reactive) |
| **Commanded Behavior** | `command-sub-agent` (CBF) | Corresponds to Operator's command operations (Command Side) |
| **Information Display** | `query-sub-agent` (IDF) | Corresponds to information query and display (Query Side) |

### 2. Structural Mapping

- **Machine Domain**: Corresponds to `machine/` directory, encapsulating Application Logic.
- **Controlled Domain**: Corresponds to `controlled-domain/` directory, encapsulating Aggregate and Domain Logic.
- **Shared Phenomena**: Achieved through explicitly defined API Interfaces and Domain Events for interaction between Machine and Domain.

### 3. Concerns Implementation

The most critical innovation of this design is the explicit **Frame Concerns** mechanism. Through `frame_concerns` and `satisfied_by` traceability in `frame.yaml`, it forces the embodiment of implicit requirements like "Reliability," "Identity," and "Synchronization" into code constraints (Design by Contract). This effectively solves the issue where GenAI-generated code easily misses non-functional requirements, achieving the core goal of "Hallucination Reduction."

---

## References

**Agent Skills**
- [Agent Skills Specification](https://agentskills.io/specification)
- [What are skills?](https://agentskills.io/what-are-skills)
- [Claude Code Skills Guide](https://code.claude.com/docs/en/skills)

**Problem Frames**
- Michael Jackson, "Problem Frames: Analysing and Structuring Software Development Problems"
