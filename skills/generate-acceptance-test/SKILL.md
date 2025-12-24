---
name: generate-acceptance-test
description: 從 analyze-frame 的 YAML 規格與 acceptance_criteria 生成/維護 BDD/ezSpec 測試骨架，確保「規格即測試」。
---

# Generate Acceptance Test Skill

## 觸發時機
- analyze-frame 產生或更新 YAML 規格後
- 需求異動需同步更新驗收測試時
- 代碼生成前，希望先鎖定可執行的驗收測試

## 核心任務
1. 解析 YAML 規格的 `acceptance_criteria`
2. 生成對應的 BDD/ezSpec 測試骨架（可選語言：Java/JUnit + Cucumber 或類似）
3. 維護規格與測試的一致性，提醒缺漏與衝突

## 工作流程
1. **解析規格**：讀取 metadata、problem_statement、acceptance_criteria。
2. **測試映射**：將每個 scenario 轉成 Given/When/Then 測試案例，標註 pre/post-conditions。
3. **輸出骨架**：
   - 檔名：`tests/acceptance/{feature-name}AcceptanceTest.{lang}`
   - 範例（Java + JUnit）：
```java
@DisplayName("{scenario}")
void {scenario_key}() {
    // Given {given}
    // When  {when}
    // Then  {then}
}
```
4. **同步檢查**：
   - 規格更新時，標記需同步更新的測試案例
   - 缺少異常/邊界場景時提出警示

## 輸出格式
- 測試骨架檔案內容（或對既有檔案的更新建議）
- 若規格不完整，列出需補的 acceptance criteria

## 檢查清單
- [ ] 每個 scenario 是否都有可執行的 Given/When/Then？
- [ ] 是否涵蓋主要與異常/邊界情境？
- [ ] 測試名稱、檔名是否對應 feature-name？
- [ ] 是否與 coding-standards、enforce-contract 一致（pre/post 驗證）？

## 常見錯誤防範
- ❌ 規格變更未同步測試
- ❌ 僅有快樂路徑，缺少異常/邊界案例
- ❌ 測試直接耦合基礎設施，未使用應用層介面

