#!/usr/bin/env python3
"""
Problem Frames Spec Validator

驗證規格目錄結構的完整性與正確性。
確保：
1. 必要檔案存在
2. YAML 格式正確
3. Frame Concerns 都有 satisfied_by 連結
4. Cross-context dependencies 有對應的 ACL 規格
5. Acceptance tests 涵蓋所有 Frame Concerns

Usage:
    python validate_spec.py <spec_dir>
    python validate_spec.py docs/specs/create-workflow/

Exit codes:
    0 - All validations passed
    1 - Validation errors found
    2 - Invalid arguments or missing files
"""

import sys
import os
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class ValidationError:
    file: str
    message: str
    severity: str = "error"  # error | warning


@dataclass
class ValidationResult:
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)
    
    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0
    
    def add_error(self, file: str, message: str):
        self.errors.append(ValidationError(file, message, "error"))
    
    def add_warning(self, file: str, message: str):
        self.warnings.append(ValidationError(file, message, "warning"))


class SpecValidator:
    """Problem Frames 規格驗證器"""
    
    REQUIRED_FILES = [
        "frame.yaml",
    ]
    
    OPTIONAL_DIRECTORIES = [
        "requirements",
        "machine",
        "controlled-domain",
        "cross-context",
        "acceptance",
        "runbook",
    ]
    
    VALID_FRAME_TYPES = [
        "CommandedBehaviorFrame",
        "InformationDisplayFrame",
        "RequiredBehaviorFrame",
        "WorkpiecesFrame",
        "TransformationFrame",
    ]
    
    def __init__(self, spec_dir: Path):
        self.spec_dir = spec_dir
        self.result = ValidationResult()
        self.frame_data: Optional[Dict[str, Any]] = None
    
    def validate(self) -> ValidationResult:
        """執行完整驗證"""
        self._check_directory_exists()
        if not self.result.is_valid:
            return self.result
        
        self._check_required_files()
        self._load_frame_yaml()
        
        if self.frame_data:
            self._validate_frame_yaml()
            self._validate_frame_concerns()
            self._validate_cross_context()
            self._validate_requirements()
            self._validate_machine()
            self._validate_controlled_domain()
            self._validate_acceptance()
        
        return self.result
    
    def _check_directory_exists(self):
        """檢查規格目錄是否存在"""
        if not self.spec_dir.exists():
            self.result.add_error(
                str(self.spec_dir),
                f"Spec directory does not exist: {self.spec_dir}"
            )
        elif not self.spec_dir.is_dir():
            self.result.add_error(
                str(self.spec_dir),
                f"Path is not a directory: {self.spec_dir}"
            )
    
    def _check_required_files(self):
        """檢查必要檔案是否存在"""
        for file in self.REQUIRED_FILES:
            file_path = self.spec_dir / file
            if not file_path.exists():
                self.result.add_error(
                    file,
                    f"Required file missing: {file}"
                )
    
    def _load_frame_yaml(self):
        """載入 frame.yaml"""
        frame_path = self.spec_dir / "frame.yaml"
        if not frame_path.exists():
            return
        
        try:
            with open(frame_path, 'r', encoding='utf-8') as f:
                self.frame_data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            self.result.add_error(
                "frame.yaml",
                f"Invalid YAML syntax: {e}"
            )
    
    def _validate_frame_yaml(self):
        """驗證 frame.yaml 結構"""
        if not self.frame_data:
            return
        
        # 檢查必要欄位
        required_fields = ["problem_frame", "frame_type", "intent"]
        for field in required_fields:
            if field not in self.frame_data:
                self.result.add_error(
                    "frame.yaml",
                    f"Missing required field: {field}"
                )
        
        # 驗證 frame_type
        frame_type = self.frame_data.get("frame_type")
        if frame_type and frame_type not in self.VALID_FRAME_TYPES:
            self.result.add_error(
                "frame.yaml",
                f"Invalid frame_type: {frame_type}. "
                f"Valid types: {', '.join(self.VALID_FRAME_TYPES)}"
            )
        
        # 檢查 operator
        if "operator" not in self.frame_data:
            self.result.add_warning(
                "frame.yaml",
                "Missing 'operator' section"
            )
        
        # 檢查 machine
        if "machine" not in self.frame_data:
            self.result.add_warning(
                "frame.yaml",
                "Missing 'machine' section"
            )
        
        # 檢查 controlled_domain
        if "controlled_domain" not in self.frame_data:
            self.result.add_warning(
                "frame.yaml",
                "Missing 'controlled_domain' section"
            )
    
    def _validate_frame_concerns(self):
        """驗證 Frame Concerns 的 satisfied_by 連結"""
        if not self.frame_data:
            return
        
        frame_concerns = self.frame_data.get("frame_concerns", [])
        
        if not frame_concerns:
            self.result.add_warning(
                "frame.yaml",
                "No frame_concerns defined"
            )
            return
        
        for fc in frame_concerns:
            fc_id = fc.get("id", "unknown")
            
            # 檢查必要欄位
            if "name" not in fc:
                self.result.add_error(
                    "frame.yaml",
                    f"Frame concern {fc_id} missing 'name'"
                )
            
            if "description" not in fc:
                self.result.add_warning(
                    "frame.yaml",
                    f"Frame concern {fc_id} missing 'description'"
                )
            
            # 檢查 satisfied_by
            satisfied_by = fc.get("satisfied_by", [])
            if not satisfied_by:
                self.result.add_error(
                    "frame.yaml",
                    f"Frame concern {fc_id} has no 'satisfied_by' links"
                )
            else:
                # 驗證 satisfied_by 連結的檔案存在
                for link in satisfied_by:
                    self._validate_satisfied_by_link(fc_id, link)
    
    def _validate_satisfied_by_link(self, fc_id: str, link: str):
        """驗證 satisfied_by 連結"""
        # 格式: file.yaml#section 或 tests#test-id
        if link.startswith("tests#"):
            # 測試連結，稍後在 acceptance 驗證
            return
        
        if "#" in link:
            file_part, section = link.split("#", 1)
        else:
            file_part = link
        
        file_path = self.spec_dir / file_part
        if not file_path.exists():
            self.result.add_warning(
                "frame.yaml",
                f"Frame concern {fc_id}: satisfied_by file not found: {file_part}"
            )
    
    def _validate_cross_context(self):
        """驗證跨 BC 依賴"""
        if not self.frame_data:
            return
        
        cross_context_deps = self.frame_data.get("cross_context_dependencies", [])
        cross_context_dir = self.spec_dir / "cross-context"
        
        for xc in cross_context_deps:
            xc_id = xc.get("id", "unknown")
            xc_name = xc.get("name", "unknown")
            
            # 檢查必要欄位
            if "source_context" not in xc:
                self.result.add_error(
                    "frame.yaml",
                    f"Cross-context {xc_id} missing 'source_context'"
                )
            
            if "target_context" not in xc:
                self.result.add_error(
                    "frame.yaml",
                    f"Cross-context {xc_id} missing 'target_context'"
                )
            
            # 檢查對應的 ACL 規格檔案
            contract_spec = xc.get("contract_spec")
            if contract_spec:
                spec_path = self.spec_dir / contract_spec
                if not spec_path.exists():
                    self.result.add_error(
                        "frame.yaml",
                        f"Cross-context {xc_id}: ACL spec file not found: {contract_spec}"
                    )
            else:
                # 嘗試找預設位置
                default_name = xc_name.lower().replace(" ", "-")
                default_path = cross_context_dir / f"{default_name}.yaml"
                if cross_context_dir.exists() and not default_path.exists():
                    self.result.add_warning(
                        "frame.yaml",
                        f"Cross-context {xc_id}: No ACL spec file found, "
                        f"expected: cross-context/{default_name}.yaml"
                    )
    
    def _validate_requirements(self):
        """驗證需求層"""
        req_dir = self.spec_dir / "requirements"
        if not req_dir.exists():
            self.result.add_warning(
                "requirements/",
                "Requirements directory not found"
            )
            return
        
        yaml_files = list(req_dir.glob("*.yaml")) + list(req_dir.glob("*.yml"))
        if not yaml_files:
            self.result.add_warning(
                "requirements/",
                "No requirement YAML files found"
            )
            return
        
        for yaml_file in yaml_files:
            self._validate_requirement_file(yaml_file)
    
    def _validate_requirement_file(self, file_path: Path):
        """驗證單個需求檔案"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            self.result.add_error(
                str(file_path.name),
                f"Invalid YAML syntax: {e}"
            )
            return
        
        if not data:
            return
        
        req = data.get("requirement", data)
        
        # 檢查是否有實作細節（不應該有）
        implementation_keywords = [
            "class", "function", "method", "interface",
            "repository", "controller", "service", "handler"
        ]
        
        description = str(req.get("description", "")).lower()
        for keyword in implementation_keywords:
            if keyword in description:
                self.result.add_warning(
                    str(file_path.name),
                    f"Requirement description may contain implementation details: '{keyword}'"
                )
    
    def _validate_machine(self):
        """驗證機器層"""
        machine_dir = self.spec_dir / "machine"
        if not machine_dir.exists():
            self.result.add_warning(
                "machine/",
                "Machine directory not found"
            )
            return
        
        # 根據 frame_type 檢查對應的規格檔案
        if not self.frame_data:
            return
        
        frame_type = self.frame_data.get("frame_type")
        
        expected_files = {
            "CommandedBehaviorFrame": ["use-case.yaml"],
            "InformationDisplayFrame": ["query.yaml"],
            "RequiredBehaviorFrame": ["reactor.yaml"],
        }
        
        if frame_type in expected_files:
            for expected in expected_files[frame_type]:
                file_path = machine_dir / expected
                if not file_path.exists():
                    self.result.add_warning(
                        f"machine/{expected}",
                        f"Expected machine spec file for {frame_type}: {expected}"
                    )
    
    def _validate_controlled_domain(self):
        """驗證領域層"""
        domain_dir = self.spec_dir / "controlled-domain"
        if not domain_dir.exists():
            self.result.add_warning(
                "controlled-domain/",
                "Controlled-domain directory not found"
            )
            return
        
        aggregate_file = domain_dir / "aggregate.yaml"
        if not aggregate_file.exists():
            self.result.add_warning(
                "controlled-domain/aggregate.yaml",
                "Aggregate specification not found"
            )
            return
        
        # 驗證 aggregate.yaml 內容
        try:
            with open(aggregate_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            self.result.add_error(
                "controlled-domain/aggregate.yaml",
                f"Invalid YAML syntax: {e}"
            )
            return
        
        if data:
            aggregate = data.get("aggregate", data)
            
            if "invariants" not in aggregate:
                self.result.add_warning(
                    "controlled-domain/aggregate.yaml",
                    "No invariants defined in aggregate"
                )
    
    def _validate_acceptance(self):
        """驗證驗收測試"""
        # 新結構：acceptance.yaml 在根目錄
        acceptance_file = self.spec_dir / "acceptance.yaml"
        
        # 向下相容：也支援舊結構 acceptance/acceptance.yaml
        if not acceptance_file.exists():
            acceptance_dir = self.spec_dir / "acceptance"
            if acceptance_dir.exists():
                acceptance_file = acceptance_dir / "acceptance.yaml"
        
        if not acceptance_file.exists():
            self.result.add_warning(
                "acceptance.yaml",
                "Acceptance specification not found (expected at root level)"
            )
            return
        
        # 驗證 acceptance.yaml
        try:
            with open(acceptance_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            self.result.add_error(
                str(acceptance_file.relative_to(self.spec_dir)),
                f"Invalid YAML syntax: {e}"
            )
            return
        
        if not data:
            return
        
        # 支援新格式 (acceptance_criteria) 和舊格式 (acceptance.scenarios)
        acceptance_criteria = data.get("acceptance_criteria", [])
        if not acceptance_criteria:
            acceptance = data.get("acceptance", data)
            acceptance_criteria = acceptance.get("scenarios", [])
        
        if not acceptance_criteria:
            self.result.add_warning(
                str(acceptance_file.relative_to(self.spec_dir)),
                "No acceptance criteria (scenarios) defined"
            )
            return
        
        # 檢查場景類型覆蓋
        types = [s.get("type") for s in acceptance_criteria]
        if "business" not in types and "happy-path" not in types:
            self.result.add_warning(
                str(acceptance_file.relative_to(self.spec_dir)),
                "No business (happy-path) scenario defined"
            )
        
        # 檢查新格式的必要欄位
        for ac in acceptance_criteria:
            ac_id = ac.get("id", "unknown")
            
            # 檢查 trace 連結
            if "trace" not in ac:
                self.result.add_warning(
                    str(acceptance_file.relative_to(self.spec_dir)),
                    f"Acceptance criteria {ac_id} missing 'trace' links to requirements/frame_concerns"
                )
            
            # 檢查 given/when/then 格式
            if "given" not in ac or "when" not in ac or "then" not in ac:
                self.result.add_warning(
                    str(acceptance_file.relative_to(self.spec_dir)),
                    f"Acceptance criteria {ac_id} missing given/when/then structure"
                )
        
        # 檢查是否涵蓋所有 Frame Concerns
        if self.frame_data:
            frame_concerns = self.frame_data.get("frame_concerns", [])
            fc_ids = {fc.get("id") for fc in frame_concerns}
            
            validated_concerns = set()
            for ac in acceptance_criteria:
                # 新格式：trace.frame_concerns
                trace = ac.get("trace", {})
                for fc in trace.get("frame_concerns", []):
                    validated_concerns.add(fc)
                
                # 舊格式：validates_concerns
                for vc in ac.get("validates_concerns", []):
                    validated_concerns.add(vc)
            
            missing = fc_ids - validated_concerns
            if missing:
                self.result.add_warning(
                    str(acceptance_file.relative_to(self.spec_dir)),
                    f"Frame concerns not covered by tests: {', '.join(missing)}"
                )


def print_result(result: ValidationResult, spec_dir: Path):
    """輸出驗證結果"""
    print(f"\n{'='*60}")
    print(f"Problem Frames Spec Validation: {spec_dir}")
    print(f"{'='*60}\n")
    
    if result.errors:
        print(f"❌ ERRORS ({len(result.errors)}):")
        print("-" * 40)
        for err in result.errors:
            print(f"  [{err.file}] {err.message}")
        print()
    
    if result.warnings:
        print(f"⚠️  WARNINGS ({len(result.warnings)}):")
        print("-" * 40)
        for warn in result.warnings:
            print(f"  [{warn.file}] {warn.message}")
        print()
    
    if result.is_valid:
        if result.warnings:
            print(f"✅ Validation PASSED with {len(result.warnings)} warning(s)")
        else:
            print("✅ Validation PASSED - All checks OK")
    else:
        print(f"❌ Validation FAILED with {len(result.errors)} error(s)")
    
    print()
    return 0 if result.is_valid else 1


def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_spec.py <spec_dir>")
        print("Example: python validate_spec.py docs/specs/create-workflow/")
        sys.exit(2)
    
    spec_dir = Path(sys.argv[1])
    
    validator = SpecValidator(spec_dir)
    result = validator.validate()
    
    exit_code = print_result(result, spec_dir)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
