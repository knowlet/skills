---
name: saga
description: 協調多個子代理完成跨 Frame 的複雜業務流程 (Saga Pattern)
---

請處理涉及多個狀態變更、事件反應或查詢組合的複雜業務流程。

1. 識別複合流程中的各個步驟及其 Frame 類型。
2. 設計 Saga 步驟與補償邏輯。
3. 使用 `runSubagent` 分派任務給對應的子代理：
   - `command-sub-agent` (CBF)
   - `query-sub-agent` (IDF)
   - `reactor-sub-agent` (RIF)
4. 確保最終一致性與錯誤回饋處理。
