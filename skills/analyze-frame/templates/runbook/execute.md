# {Feature Name} Runbook

## 概述

本文件提供 `{FeatureName}` 功能的開發與驗證指南。

## 前置條件檢查

開始開發前，請確認：

- [ ] `requirements/` 需求已確認並審核
- [ ] `frame.yaml` 問題框架已定義
- [ ] `frame_concerns` 都有 `satisfied_by` 連結
- [ ] `cross_context_dependencies` 已識別 (若有)
- [ ] `acceptance/acceptance.yaml` 驗收測試已撰寫

## 驗證規格

執行規格驗證器：

```bash
python ~/.claude/skills/analyze-frame/scripts/validate_spec.py docs/specs/{feature-name}/
```

確保沒有 ERROR，WARNING 可以稍後處理。

## 生成步驟

### Step 1: 生成 Domain 層

根據 `controlled-domain/aggregate.yaml` 生成：

```
目標位置: src/domain/
├── aggregates/
│   └── {Aggregate}.ts
├── entities/
│   └── {Entity}.ts
├── value-objects/
│   ├── {Aggregate}Id.ts
│   └── {ValueObject}.ts
├── events/
│   └── {Aggregate}CreatedEvent.ts
├── repositories/
│   └── {Aggregate}Repository.ts (interface)
└── services/
    └── AuthorizationService.ts (interface, if XC exists)
```

**提示 Claude:**
```
根據 docs/specs/{feature-name}/controlled-domain/aggregate.yaml
請用 TypeScript 生成 Domain 層的程式碼
```

### Step 2: 生成 Application 層

根據 `machine/use-case.yaml` 生成：

```
目標位置: src/application/
└── use-cases/
    └── {FeatureName}UseCase.ts
```

**提示 Claude:**
```
根據 docs/specs/{feature-name}/machine/use-case.yaml
請用 TypeScript 生成 {FeatureName}UseCase
確保整合 cross-context/authorization.yaml 的 ACL
```

### Step 3: 生成 Infrastructure 層

根據規格生成：

```
目標位置: src/infrastructure/
├── repositories/
│   └── Postgres{Aggregate}Repository.ts
├── acl/
│   └── AccessControlAuthorizationAdapter.ts (if XC exists)
└── controllers/
    └── {Feature}Controller.ts
```

**提示 Claude:**
```
根據 docs/specs/{feature-name}/ 規格目錄
請生成 Infrastructure 層的實作
```

### Step 4: 生成驗收測試

根據 `acceptance/acceptance.yaml` 生成：

```
目標位置: 
├── docs/specs/{feature-name}/acceptance/generated/
│   └── {feature-name}.feature
└── tests/acceptance/
    └── {FeatureName}.spec.ts
```

**提示 Claude:**
```
根據 docs/specs/{feature-name}/acceptance/acceptance.yaml
請生成 ezSpec .feature 檔案和 TypeScript 測試骨架
```

## 品質驗證

### 驗證 Frame Concerns 覆蓋

確認每個 Frame Concern 都有對應的實作：

| Frame Concern | 規格位置 | 實作位置 | 測試 |
|---------------|----------|----------|------|
| FC1 | aggregate.yaml#invariants.shared.INV1 | Aggregate.validateInvariants() | AT1 |
| FC2 | use-case.yaml#transaction_boundary | UseCase transaction handling | AT4 |

### 執行測試

```bash
# 執行驗收測試
npm test -- --grep "Feature: {FeatureName}"

# 執行所有相關測試
npm test -- tests/acceptance/{FeatureName}.spec.ts
```

### 架構檢查

```
請用 arch-guard 檢查 src/domain/ 和 src/application/ 的依賴是否符合 Clean Architecture
```

## 重新生成（品質改進）

當規格更新後，執行重新生成：

```bash
# 1. 刪除舊代碼
rm -rf src/application/use-cases/{FeatureName}*
rm -rf src/domain/aggregates/{Aggregate}*

# 2. 重新驗證規格
python ~/.claude/skills/analyze-frame/scripts/validate_spec.py docs/specs/{feature-name}/

# 3. 重新生成（提示 Claude）
# 根據更新後的 docs/specs/{feature-name}/ 規格目錄
# 請重新生成所有相關程式碼

# 4. 比較差異
git diff HEAD~1
```

## 常見問題

### Q: Frame Concern 沒有 satisfied_by 連結怎麼辦？

A: 每個 Frame Concern 都必須有至少一個 `satisfied_by` 連結。如果找不到對應的實作：
1. 檢查是否遺漏了 invariant 定義
2. 檢查是否需要新增測試案例

### Q: 跨 BC 依賴如何處理？

A: 
1. 在 `cross-context/` 目錄建立 ACL 規格
2. 在 Domain 層定義介面
3. 在 Infrastructure 層實作 Adapter
4. 在 Use Case 中注入並使用

### Q: 如何確保代碼品質？

A:
1. 使用 `validate_spec.py` 驗證規格完整性
2. 使用 `arch-guard` 檢查架構層次
3. 使用 `enforce-contract` 驗證契約
4. 執行驗收測試確保功能正確
