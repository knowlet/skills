---
name: analyze-frame
description: 當接收到新需求或 Event Storming 產出後觸發。分析問題類別（CBF/IDF/RIF），並生成 YAML 規格書。實現「規格即文檔、文檔即規格」。
---

# Analyze Frame Skill

## 觸發時機

- 接收到新需求描述時
- Event Storming 工作坊產出後
- 使用者要求分析問題框架時

## 核心任務

將需求分析為 Problem Frames 的三種類別，並輸出結構化 YAML 規格書。

## Problem Frame 類別定義

### CBF (Command-Based Frame) - 命令框架
- **特徵**：使用者發出命令，系統執行狀態變更
- **對應 Sub-agent**：`command-sub-agent`
- **典型場景**：建立訂單、更新資料、執行交易
- **CQRS 角色**：Command Side

### IDF (Information Display Frame) - 資訊顯示框架
- **特徵**：使用者查詢資訊，系統回傳資料（無狀態變更）
- **對應 Sub-agent**：`query-sub-agent`
- **典型場景**：查詢報表、搜尋資料、讀取詳情
- **CQRS 角色**：Query Side

### RIF (Reactive/Integration Frame) - 反應式框架
- **特徵**：系統對事件做出反應，通常是非同步處理
- **對應 Sub-agent**：`reactor-sub-agent`
- **典型場景**：事件監聽、訊息處理、系統整合

## 分析流程

1. **識別 Actor**：誰發起這個需求？
2. **識別 Action**：要執行什麼動作？
3. **識別 Effect**：對系統狀態有什麼影響？
4. **分類 Frame**：根據上述判斷屬於 CBF/IDF/RIF
5. **生成規格書**：輸出標準化 YAML

## YAML 規格書範本

在 `docs/specs/` 目錄下生成規格書，遵循以下格式：

```yaml
# docs/specs/{feature-name}.yaml
metadata:
  name: "{feature-name}"
  version: "1.0.0"
  created_at: "{ISO-8601-timestamp}"
  frame_type: "CBF | IDF | RIF"
  sub_agent: "command-sub-agent | query-sub-agent | reactor-sub-agent"

problem_statement:
  actor: "{誰發起}"
  goal: "{要達成什麼}"
  context: "{在什麼情境下}"

domain:
  aggregate: "{聚合根名稱}"
  bounded_context: "{限界上下文}"
  entities: []
  value_objects: []

acceptance_criteria:
  # BDD/ezSpec 格式
  - scenario: "{場景名稱}"
    given: "{前置條件}"
    when: "{觸發動作}"
    then: "{預期結果}"

technical_constraints:
  - "{技術約束 1}"
  - "{技術約束 2}"

contracts:
  pre_conditions:
    - "{輸入參數必須不為 null}"
    - "{數量必須大於 0}"
  post_conditions:
    - "{產出結果必須包含 ID}"
    - "{狀態必須變更為 CREATED}"
  invariants:
    - "{訂單總金額必須等於細項總和}"
```

## 輸出要求

1. **規格即文檔**：YAML 必須足夠詳細，讓 Sub-agent 可直接依據執行
2. **人類可讀**：同時確保架構師與開發者能閱讀理解
3. **版本化**：每次修改需更新版本號
4. **可追溯**：保留完整的需求到規格的對應關係

## 範例分析

### 輸入需求
> 「使用者可以建立新訂單，選擇商品並指定數量」

### 分析結果
```yaml
metadata:
  name: "create-order"
  version: "1.0.0"
  created_at: "2024-12-24T10:00:00Z"
  frame_type: "CBF"
  sub_agent: "command-sub-agent"

problem_statement:
  actor: "Customer"
  goal: "建立包含商品的新訂單"
  context: "在購物流程中完成下單"

domain:
  aggregate: "Order"
  bounded_context: "OrderManagement"
  entities:
    - "Order"
    - "OrderItem"
  value_objects:
    - "OrderId"
    - "Quantity"
    - "Money"

acceptance_criteria:
  - scenario: "成功建立訂單"
    given: "使用者已登入且購物車有商品"
    when: "使用者點擊確認訂單"
    then: "系統建立訂單並回傳訂單編號"
  
  - scenario: "商品庫存不足"
    given: "使用者選擇的商品庫存為 0"
    when: "使用者嘗試建立訂單"
    then: "系統拒絕並提示庫存不足"

technical_constraints:
  - "訂單建立必須是原子操作"
  - "需發送 OrderCreated 領域事件"
```

## 品質檢查清單

- [ ] Frame 類別判斷是否正確？
- [ ] 是否明確識別出 Aggregate Root？
- [ ] Acceptance Criteria 是否可測試？
- [ ] 是否包含完整的 Contracts (Pre/Post/Invariants)？
- [ ] 是否涵蓋主要的異常場景？
- [ ] Sub-agent 對應是否正確？
