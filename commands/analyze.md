---
name: analyze
description: 分析新需求的問題框架 (Problem Frames) 並生成規格目錄
---

請根據使用者提供的新需求描述，使用 `skills/analyze-frame/SKILL.md` 的邏輯進行分析。

1. 識別 Operator, Machine, Controlled Domain。
2. 判斷 Frame Type (CBF, IDF, RIF, WPF, TF)。
3. 在 `docs/specs/{feature-name}/` 下生成完整的規格目錄結構（包含 frame.yaml, machine/, controlled-domain/, cross-context/, acceptance/, runbook/）。
4. 使用 `skills/analyze-frame/templates/` 下的範本進行填充。
5. 提示使用者可以使用 `skills/analyze-frame/scripts/validate_spec.py` 驗證規格。
