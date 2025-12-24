# Problem Frames Skills

基於 **Problem Frames** 理論設計的 Agent Skills，透過多層次約束架構減少 AI 幻覺，實現「規格即文檔、文檔即規格」。

---

## 目錄

- [快速開始](#快速開始)
- [設計哲學](#設計哲學)
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
│  Event Storming → BDD 驗收測試 →「AI 要解決什麼問題？」            │
├─────────────────────────────────────────────────────────────────┤
│  大尺度約束 (Architecture)                                       │
│  Clean Architecture + DDD + CQRS →「程式碼該放在哪裡？」          │
├─────────────────────────────────────────────────────────────────┤
│  中尺度約束 (Sub-agent)                                          │
│  command / query / reactor →「AI 當下該扮演什麼角色？」           │
├─────────────────────────────────────────────────────────────────┤
│  小尺度約束 (Coding Standards)                                   │
│  Input/Output 模式、DI 規範 →「程式碼該長什麼樣子？」              │
├─────────────────────────────────────────────────────────────────┤
│  微尺度約束 (Design by Contract)                                 │
│  pre/post-conditions、invariants →「邊界條件是什麼？」            │
└─────────────────────────────────────────────────────────────────┘
                                ↓
              縮小 AI 幻覺的解題空間 (Hallucination Reduction)
```

### Problem Frame 類型

| Frame | 說明 | Sub-agent |
|-------|------|-----------|
| **CBF** | 使用者發出命令，系統執行狀態變更 | `command-sub-agent` |
| **IDF** | 使用者查詢資訊，系統回傳資料 | `query-sub-agent` |
| **RIF** | 系統對事件做出反應，非同步處理 | `reactor-sub-agent` |

---

## Skills 清單

### 核心 Skills

| Skill | 觸發時機 | 說明 |
|-------|---------|------|
| [`analyze-frame`](skills/analyze-frame/SKILL.md) | 新需求 | 分析問題框架，生成 YAML 規格書 |
| [`saga-orchestrator`](skills/saga-orchestrator/SKILL.md) | 跨 Frame 流程 | 協調多個 Sub-agent，處理 Saga 模式 |

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
│                  判斷 Frame 類型 (CBF/IDF/RIF)                    │
└───────────────────────────┬─────────────────────────────────────┘
                            │
          ┌─────────────────┼─────────────────┐
          ▼                 ▼                 ▼
    ┌───────────┐     ┌───────────┐     ┌───────────┐
    │  command  │     │   query   │     │  reactor  │
    │ sub-agent │     │ sub-agent │     │ sub-agent │
    └─────┬─────┘     └─────┬─────┘     └─────┬─────┘
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

### 跨 Frame 流程 (Saga)

```
複雜業務流程 (下單 + 付款 + 通知 + 報表)
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│                      saga-orchestrator                           │
│                    拆解 Saga 步驟與補償邏輯                        │
└───────────────────────────┬─────────────────────────────────────┘
                            │ runSubagent
                            │
    ┌───────────────────────┼───────────────────────┐
    ▼                       ▼                       ▼
┌─────────┐  event   ┌─────────┐  event   ┌─────────┐
│ Step 1  │────────▶ │ Step 2  │────────▶ │ Step 3  │
│  (CBF)  │          │  (RIF)  │          │  (IDF)  │
└────┬────┘          └────┬────┘          └─────────┘
     │                    │
     ▼                    ▼
 compensation        compensation
  if failed           if failed
```

### Claude Code Sub-agent 分派架構

```
┌────────────────────────────────────────────────────────┐
│                   Claude Code Agent                     │
│                                                         │
│    saga-orchestrator                                    │
│          │                                              │
│          │ runSubagent                                  │
│          │                                              │
│    ┌─────┴─────┬─────────────┬──────────────┐          │
│    ▼           ▼             ▼              ▼          │
│ command-   query-      reactor-      coding-           │
│ sub-agent  sub-agent   sub-agent     standards         │
│    │           │             │              │          │
│    └───────────┴─────────────┴──────────────┘          │
│                       │                                 │
│                       ▼                                 │
│                enforce-contract                         │
└────────────────────────────────────────────────────────┘
```

---

## 使用範例

### 範例 1：分析新需求

```
我有一個新需求：「使用者可以建立新訂單，選擇商品並指定數量」
請幫我分析這個需求的 Problem Frame 類型並產生規格書
```

→ Claude 使用 `analyze-frame`，判斷為 CBF，輸出 YAML 規格書

### 範例 2：生成代碼

```
根據 docs/specs/create-order.yaml 規格書，
請用 TypeScript 生成 CreateOrderUseCase 的程式碼骨架
```

→ Claude 使用 `command-sub-agent` + `coding-standards` + `enforce-contract`

### 範例 3：複雜業務流程

```
設計一個完整的訂單流程：下單 → 扣庫存 → 付款 → 通知 → 更新報表
請幫我設計 Saga 架構
```

→ Claude 使用 `saga-orchestrator` 協調多個 sub-agent

### 範例 4：架構審查

```
請審查 src/domain/OrderService.ts 是否符合 Clean Architecture 原則
```

→ Claude 使用 `arch-guard` 檢查依賴方向和層次邊界

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
- [Skill Authoring Best Practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)

**範例庫**
- [anthropics/skills](https://github.com/anthropics/skills)
- [openai/skills](https://github.com/openai/skills)
