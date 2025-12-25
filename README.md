# Problem Frames Skills

基於 **Problem Frames** 理論設計的 Agent Skills，透過多層次約束架構減少 AI 幻覺，實現「需求與實作分離」、「規格即文檔、文檔即規格」。

---

## 目錄

- [快速開始](#快速開始)
- [設計哲學](#設計哲學)
- [規格目錄結構](#規格目錄結構)
- [Skills 清單](#skills-清單)
- [工作流程](#工作流程)
- [使用範例](#使用範例)
- [參考資料](#參考資料)

---

## 快速開始

### 安裝

**Personal Skills（個人使用）**
```bash
cp -r skills/* ~/.claude/skills/
```

**Project Skills（團隊共享）**
```bash
mkdir -p .claude/skills
cp -r /path/to/this/repo/skills/* .claude/skills/
git add .claude/skills/ && git commit -m "Add Problem Frames skills"
```

### 驗證

啟動 Claude Code 後詢問：
```
What Skills are available?
```

---

## 設計哲學

### 多層次約束架構

```
┌─────────────────────────────────────────────────────────────────┐
│  需求約束 (Requirement)                                          │
│  requirements/*.yaml → 純業務語言，無實作細節                     │
├─────────────────────────────────────────────────────────────────┤
│  框架約束 (Frame)                                                │
│  frame.yaml → Frame Concerns + Cross-Context Dependencies       │
├─────────────────────────────────────────────────────────────────┤
│  機器約束 (Machine)                                              │
│  machine/*.yaml → Use Case / Query / Reactor 規格               │
├─────────────────────────────────────────────────────────────────┤
│  領域約束 (Controlled Domain)                                    │
│  controlled-domain/*.yaml → Aggregate + Invariants              │
├─────────────────────────────────────────────────────────────────┤
│  驗收約束 (Acceptance)                                           │
│  acceptance/*.yaml → BDD 場景 + validates_concerns              │
└─────────────────────────────────────────────────────────────────┘
                                ↓
              縮小 AI 幻覺的解題空間 (Hallucination Reduction)
```

### Problem Frame 類型

| Frame | 說明 | Sub-agent |
|-------|------|-----------|
| **CBF** | Commanded Behavior - Operator 發出命令，系統執行狀態變更 | `command-sub-agent` |
| **IDF** | Information Display - 使用者查詢資訊，系統回傳資料 | `query-sub-agent` |
| **RIF** | Required Behavior - 系統對事件做出反應，非同步處理 | `reactor-sub-agent` |
| **WPF** | Workpieces - 對工作產物進行編輯與管理 | - |
| **TF** | Transformation - 輸入資料經過轉換產生輸出 | - |

---

## 規格目錄結構

每個 Feature 對應一個規格目錄：

```
docs/specs/{feature-name}/
├── frame.yaml                 # 問題框架定義 (核心)
│   ├── frame_concerns         # 關注點 + satisfied_by 追溯
│   └── cross_context_deps     # 跨 BC 依賴
│
├── requirements/              # 需求層 (What) - 純業務語言
│   └── req-1-{feature}.yaml
│
├── machine/                   # 機器層 (How) - Application 層
│   ├── machine.yaml           # Machine 定義
│   ├── controller.yaml        # API 入口規格
│   ├── use-case.yaml          # Use Case 規格 (CBF)
│   ├── query.yaml             # Query 規格 (IDF)
│   └── reactor.yaml           # Reactor 規格 (RIF)
│
├── controlled-domain/         # 領域層 - Domain 層
│   └── aggregate.yaml         # Aggregate + Invariants
│
├── cross-context/             # 跨 Bounded Context 依賴
│   └── {context-name}.yaml    # ACL 定義
│
├── acceptance/                # 驗收測試
│   ├── acceptance.yaml        # 測試規格
│   └── generated/             # AI 生成的 ezSpec
│       └── {feature}.feature
│
└── runbook/
    └── execute.md             # 執行指南
```

---

## Skills 清單

### 核心 Skills

| Skill | 觸發時機 | 說明 |
|-------|---------|------|
| [`analyze-frame`](skills/analyze-frame/SKILL.md) | 新需求 | 分析問題框架，生成規格目錄結構 |
| [`saga-orchestrator`](skills/saga-orchestrator/SKILL.md) | 跨 Frame 流程 | 協調多個 Sub-agent，處理 Saga 模式 |
| [`cross-context`](skills/cross-context/SKILL.md) | 跨 BC 依賴 | 設計 Anti-Corruption Layer |

### Sub-agents

| Skill | Frame | 說明 |
|-------|-------|------|
| [`command-sub-agent`](skills/command-sub-agent/SKILL.md) | CBF | Use Case、Aggregate、Domain Event |
| [`query-sub-agent`](skills/query-sub-agent/SKILL.md) | IDF | Query Handler、Read Model、快取 |
| [`reactor-sub-agent`](skills/reactor-sub-agent/SKILL.md) | RIF | Event Handler、冪等性、重試機制 |

### 品質守護

| Skill | 說明 |
|-------|------|
| [`arch-guard`](skills/arch-guard/SKILL.md) | 確保 Clean Architecture + DDD + CQRS 層次 |
| [`coding-standards`](skills/coding-standards/SKILL.md) | 強制執行編碼規範 |
| [`enforce-contract`](skills/enforce-contract/SKILL.md) | 驗證 pre/post-conditions 與 invariants |
| [`generate-acceptance-test`](skills/generate-acceptance-test/SKILL.md) | 生成 BDD/ezSpec 測試骨架 |

### 多語言支援

| 語言 | 參考文件 |
|-----|---------|
| Java | [`coding-standards/SKILL.md`](skills/coding-standards/SKILL.md) |
| TypeScript | [`coding-standards/references/TYPESCRIPT.md`](skills/coding-standards/references/TYPESCRIPT.md) |
| Go | [`coding-standards/references/GOLANG.md`](skills/coding-standards/references/GOLANG.md) |

---

## 工作流程

### 單一 Frame 流程

```
需求輸入
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│                        analyze-frame                             │
│            生成規格目錄 (frame.yaml + 各層 YAML)                  │
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
          │   cross-context (若有跨 BC 依賴)   │
          │                 │                 │
          └─────────────────┼─────────────────┘
                            │
          ┌─────────────────┴─────────────────┐
          │           品質守護層               │
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

### Frame Concerns 可追溯性

```yaml
# frame.yaml
frame_concerns:
  - id: FC1
    name: "Structure Integrity"
    description: "SwimLane must be under a Stage"
    satisfied_by:
      - controlled-domain/aggregate.yaml#invariants.shared
      - tests#lane-hierarchy

# 生成的代碼必須實作 FC1
# Aggregate.validateInvariants() 強制執行
```

### 跨 BC 依賴處理

```
analyze-frame
    │
    ├── 識別 cross_context_dependencies
    │       └── XC1: Authorization (AccessControl BC)
    │
    └── cross-context Skill
            │
            ├── 設計 ACL 規格 (cross-context/authorization.yaml)
            │
            └── command-sub-agent
                    └── 在 Use Case 中整合 AuthorizationService
```

---

## 使用範例

### 範例 1：分析新需求

```
我有一個新需求：「使用者可以建立新的 Workflow，並關聯到指定的 Board」
請幫我分析這個需求的 Problem Frame 類型並產生規格目錄
```

→ Claude 使用 `analyze-frame`，判斷為 CBF，輸出完整規格目錄

### 範例 2：處理跨 BC 依賴

```
這個需求需要權限檢查：「只有 Board Member 才能建立 Workflow」
權限管理在 AccessControl BC，請設計 ACL
```

→ Claude 使用 `cross-context`，設計 Anti-Corruption Layer

### 範例 3：生成代碼

```
根據 docs/specs/create-workflow/ 規格目錄，
請用 TypeScript 生成 CreateWorkflowUseCase 的程式碼
```

→ Claude 使用 `command-sub-agent`，讀取規格目錄生成代碼

### 範例 4：生成驗收測試

```
根據 docs/specs/create-workflow/acceptance/acceptance.yaml
請生成 ezSpec 測試檔案
```

→ Claude 使用 `generate-acceptance-test`，生成 .feature 和測試骨架

### 範例 5：重新生成代碼

```
規格已更新，請刪除舊代碼並重新生成：
- 刪除 src/application/use-cases/CreateWorkflow*
- 刪除 src/domain/aggregates/Workflow*
- 根據更新後的規格重新生成
```

→ Claude 重新讀取規格目錄，生成更新後的代碼

---

## How Skills Work

Skills 是一種開放格式，讓 Agent 能動態載入專業知識與能力。

### Progressive Disclosure

| 階段 | 說明 | Token 消耗 |
|------|------|-----------|
| **Discovery** | 啟動時只載入 `name` + `description` | ~100/skill |
| **Activation** | 任務匹配時載入完整 `SKILL.md` | < 5000 |
| **Execution** | 按需載入 `references/`、`scripts/` | 依需求 |

### Skill 目錄結構

```
skill-name/
├── SKILL.md          # Required: 指令 + metadata
├── scripts/          # Optional: 可執行腳本
├── references/       # Optional: 參考文檔
└── assets/           # Optional: 範本、資源
```

---

## 參考資料

**Agent Skills**
- [Agent Skills Specification](https://agentskills.io/specification)
- [What are skills?](https://agentskills.io/what-are-skills)
- [Claude Code Skills Guide](https://code.claude.com/docs/en/skills)

**Problem Frames**
- Michael Jackson, "Problem Frames: Analysing and Structuring Software Development Problems"
