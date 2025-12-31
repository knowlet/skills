#!/usr/bin/env python3
"""
Acceptance Test Generator

從 acceptance.yaml 生成各語言的 BDD 測試骨架。
支援新格式 (acceptance_criteria) 和舊格式 (scenarios)。

Usage:
    python generate_tests.py <spec_dir> --lang <language> [--output <dir>]
    python generate_tests.py docs/specs/create-workflow/ --lang typescript
    python generate_tests.py docs/specs/create-workflow/ --lang go --output tests/acceptance/

Supported languages:
    - gherkin: Generate .feature file
    - typescript: Cucumber.js step definitions
    - go: Ginkgo test file
    - rust: cucumber-rs test file
    - java: ezSpec fluent API (placeholder)

Exit codes:
    0 - Generation successful
    1 - Generation failed
    2 - Invalid arguments
"""

import sys
import os
import yaml
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class AcceptanceCriteria:
    """Parsed acceptance criteria"""
    id: str
    type: str
    test_tier: str
    name: str
    trace: Dict[str, List[str]]
    tests_anchor: List[str]
    given: List[str]
    when: List[str]
    then: List[str]
    and_clauses: List[str]
    examples: List[Dict[str, str]]


class AcceptanceParser:
    """Parser for acceptance.yaml - supports both new and old formats"""
    
    def __init__(self, spec_dir: Path):
        self.spec_dir = spec_dir
        self.feature_name = spec_dir.name
        self.criteria: List[AcceptanceCriteria] = []
        self.raw_data: Dict[str, Any] = {}
    
    def parse(self) -> bool:
        """Parse acceptance.yaml file"""
        # Try new location first (root level)
        acceptance_file = self.spec_dir / "acceptance.yaml"
        
        # Fallback to old location
        if not acceptance_file.exists():
            acceptance_file = self.spec_dir / "acceptance" / "acceptance.yaml"
        
        if not acceptance_file.exists():
            print(f"ERROR: acceptance.yaml not found in {self.spec_dir}", file=sys.stderr)
            return False
        
        try:
            with open(acceptance_file, 'r', encoding='utf-8') as f:
                self.raw_data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            print(f"ERROR: Invalid YAML in {acceptance_file}: {e}", file=sys.stderr)
            return False
        
        self._parse_criteria()
        return len(self.criteria) > 0
    
    def _parse_criteria(self):
        """Parse acceptance criteria from either format"""
        # New format: acceptance_criteria list
        criteria_list = self.raw_data.get("acceptance_criteria", [])
        
        # Old format: acceptance.scenarios
        if not criteria_list:
            acceptance = self.raw_data.get("acceptance", {})
            criteria_list = acceptance.get("scenarios", [])
        
        for item in criteria_list:
            ac = self._parse_single_criteria(item)
            if ac:
                self.criteria.append(ac)
    
    def _parse_single_criteria(self, item: Dict[str, Any]) -> Optional[AcceptanceCriteria]:
        """Parse a single acceptance criteria item"""
        # Handle both formats
        ac_id = item.get("id", "AC0")
        ac_type = item.get("type", "business")
        test_tier = item.get("test_tier", "usecase")
        name = item.get("name", "")
        
        # Trace - new format
        trace = item.get("trace", {})
        if not trace:
            # Old format: validates_concerns, validates_contracts
            trace = {
                "requirement": [],
                "frame_concerns": item.get("validates_concerns", [])
            }
        
        tests_anchor = item.get("tests_anchor", [])
        
        # Given/When/Then - new format uses simple string lists
        given = self._normalize_clauses(item.get("given", []))
        when = self._normalize_clauses(item.get("when", []))
        then = self._normalize_clauses(item.get("then", []))
        and_clauses = self._normalize_clauses(item.get("and", []))
        
        examples = item.get("examples", [])
        
        return AcceptanceCriteria(
            id=ac_id,
            type=ac_type,
            test_tier=test_tier,
            name=name,
            trace=trace,
            tests_anchor=tests_anchor,
            given=given,
            when=when,
            then=then,
            and_clauses=and_clauses,
            examples=examples
        )
    
    def _normalize_clauses(self, clauses: List[Any]) -> List[str]:
        """Normalize clauses to string list (handle old format with dicts)"""
        result = []
        for clause in clauses:
            if isinstance(clause, str):
                result.append(clause)
            elif isinstance(clause, dict):
                # Old format: {"condition": "...", "setup": "..."}
                text = clause.get("condition") or clause.get("action") or clause.get("expectation", "")
                if text:
                    result.append(text)
        return result


class GherkinGenerator:
    """Generate .feature files"""
    
    def generate(self, parser: AcceptanceParser) -> str:
        lines = [
            f"# Auto-generated from acceptance.yaml - DO NOT EDIT DIRECTLY",
            f"# Last generated: {datetime.now().isoformat()}",
            f"# Feature: {parser.feature_name}",
            "",
            f"@feature-{parser.feature_name}",
            f"Feature: {self._humanize(parser.feature_name)}",
            "",
        ]
        
        for ac in parser.criteria:
            lines.extend(self._generate_scenario(ac))
            lines.append("")
        
        return "\n".join(lines)
    
    def _generate_scenario(self, ac: AcceptanceCriteria) -> List[str]:
        lines = []
        
        # Tags
        tags = [f"@{ac.id}"]
        if ac.type:
            tags.append(f"@{ac.type}")
        if ac.test_tier:
            tags.append(f"@{ac.test_tier}")
        lines.append(f"  {' '.join(tags)}")
        
        # Trace comment
        if ac.trace.get("requirement"):
            lines.append(f"  # Trace: {', '.join(ac.trace['requirement'])}")
        if ac.trace.get("frame_concerns"):
            lines.append(f"  # Frame Concerns: {', '.join(ac.trace['frame_concerns'])}")
        
        # Scenario
        has_examples = len(ac.examples) > 0
        keyword = "Scenario Outline" if has_examples else "Scenario"
        lines.append(f"  {keyword}: {ac.name}")
        
        # Given
        for i, clause in enumerate(ac.given):
            prefix = "Given" if i == 0 else "And"
            lines.append(f"    {prefix} {clause}")
        
        # When
        for i, clause in enumerate(ac.when):
            prefix = "When" if i == 0 else "And"
            lines.append(f"    {prefix} {clause}")
        
        # Then
        for i, clause in enumerate(ac.then):
            prefix = "Then" if i == 0 else "And"
            lines.append(f"    {prefix} {clause}")
        
        # And
        for clause in ac.and_clauses:
            lines.append(f"    And {clause}")
        
        # Examples
        if has_examples:
            lines.append("")
            lines.append("    Examples:")
            headers = list(ac.examples[0].keys())
            lines.append(f"      | {' | '.join(headers)} |")
            for example in ac.examples:
                values = [str(example.get(h, "")) for h in headers]
                lines.append(f"      | {' | '.join(values)} |")
        
        return lines
    
    def _humanize(self, name: str) -> str:
        return name.replace("-", " ").replace("_", " ").title()


class TypeScriptGenerator:
    """Generate Cucumber.js step definitions"""
    
    def generate(self, parser: AcceptanceParser) -> str:
        lines = [
            "// Auto-generated from acceptance.yaml",
            f"// Feature: {parser.feature_name}",
            f"// Generated: {datetime.now().isoformat()}",
            "",
            "import { Given, When, Then, Before } from '@cucumber/cucumber';",
            "import { expect } from 'chai';",
            "",
            "interface World {",
            "  input: Record<string, unknown>;",
            "  result: unknown;",
            "  error: Error | null;",
            "}",
            "",
            "Before(function(this: World) {",
            "  this.input = {};",
            "  this.result = null;",
            "  this.error = null;",
            "});",
            "",
        ]
        
        # Collect unique steps
        given_steps = set()
        when_steps = set()
        then_steps = set()
        
        for ac in parser.criteria:
            given_steps.update(ac.given)
            when_steps.update(ac.when)
            then_steps.update(ac.then + ac.and_clauses)
        
        # Generate step definitions
        lines.append("// ===== Given Steps =====")
        lines.append("")
        for step in sorted(given_steps):
            lines.extend(self._generate_step("Given", step))
            lines.append("")
        
        lines.append("// ===== When Steps =====")
        lines.append("")
        for step in sorted(when_steps):
            lines.extend(self._generate_step("When", step))
            lines.append("")
        
        lines.append("// ===== Then Steps =====")
        lines.append("")
        for step in sorted(then_steps):
            lines.extend(self._generate_step("Then", step))
            lines.append("")
        
        return "\n".join(lines)
    
    def _generate_step(self, step_type: str, step_text: str) -> List[str]:
        # Extract placeholders like <boardId>
        import re
        placeholders = re.findall(r'<(\w+)>', step_text)
        
        # Convert to regex pattern
        pattern = re.sub(r'<\w+>', '{string}', step_text)
        
        # Generate function signature
        params = ", ".join([f"{p}: string" for p in placeholders])
        
        lines = [
            f"{step_type}(",
            f"  '{pattern}',",
        ]
        
        if placeholders:
            lines.append(f"  function(this: World, {params}) {{")
        else:
            lines.append(f"  function(this: World) {{")
        
        lines.append(f"    // TODO: Implement step - {step_text}")
        lines.append(f"    throw new Error('Step not implemented');")
        lines.append(f"  }}")
        lines.append(f");")
        
        return lines


class GinkgoGenerator:
    """Generate Ginkgo test file"""
    
    def generate(self, parser: AcceptanceParser) -> str:
        package_name = parser.feature_name.replace("-", "_")
        
        lines = [
            "// Auto-generated from acceptance.yaml",
            f"// Feature: {parser.feature_name}",
            f"// Generated: {datetime.now().isoformat()}",
            "",
            f"package {package_name}_test",
            "",
            "import (",
            '    "testing"',
            "",
            '    . "github.com/onsi/ginkgo/v2"',
            '    . "github.com/onsi/gomega"',
            ")",
            "",
            f'func Test{self._pascal_case(parser.feature_name)}(t *testing.T) {{',
            "    RegisterFailHandler(Fail)",
            f'    RunSpecs(t, "{self._humanize(parser.feature_name)} Suite")',
            "}",
            "",
            f'var _ = Describe("Feature: {self._humanize(parser.feature_name)}", func() {{',
            "",
        ]
        
        for ac in parser.criteria:
            lines.extend(self._generate_describe(ac))
            lines.append("")
        
        lines.append("})")
        
        return "\n".join(lines)
    
    def _generate_describe(self, ac: AcceptanceCriteria) -> List[str]:
        lines = []
        
        # Labels
        labels = [f'"{ac.id}"']
        if ac.type:
            labels.append(f'"{ac.type}"')
        
        lines.append(f'    // Trace: {ac.trace.get("requirement", [])}')
        lines.append(f'    // Frame Concerns: {ac.trace.get("frame_concerns", [])}')
        lines.append(f'    Describe("Scenario: {ac.name}", Label({", ".join(labels)}), func() {{')
        
        # Given context
        if ac.given:
            given_text = " AND ".join(ac.given[:2])  # First two for readability
            lines.append(f'        When("{given_text}", func() {{')
            lines.append(f'            BeforeEach(func() {{')
            for g in ac.given:
                lines.append(f'                // Given: {g}')
            lines.append(f'            }})')
            lines.append("")
        
        # Then expectations
        for t in ac.then:
            lines.append(f'            It("{t}", func() {{')
            lines.append(f'                // TODO: Implement assertion')
            lines.append(f'                Expect(true).To(BeTrue())')
            lines.append(f'            }})')
            lines.append("")
        
        for a in ac.and_clauses:
            lines.append(f'            It("{a}", func() {{')
            lines.append(f'                // TODO: Implement assertion')
            lines.append(f'                Expect(true).To(BeTrue())')
            lines.append(f'            }})')
            lines.append("")
        
        if ac.given:
            lines.append(f'        }})')
        
        lines.append(f'    }})')
        
        return lines
    
    def _pascal_case(self, name: str) -> str:
        return "".join(word.capitalize() for word in name.replace("-", "_").split("_"))
    
    def _humanize(self, name: str) -> str:
        return name.replace("-", " ").replace("_", " ").title()


class RustGenerator:
    """Generate cucumber-rs test file"""
    
    def generate(self, parser: AcceptanceParser) -> str:
        mod_name = parser.feature_name.replace("-", "_")
        
        lines = [
            "// Auto-generated from acceptance.yaml",
            f"// Feature: {parser.feature_name}",
            f"// Generated: {datetime.now().isoformat()}",
            "",
            "use cucumber::{given, when, then, World};",
            "use async_trait::async_trait;",
            "",
            "// ===== World Definition =====",
            "",
            "#[derive(Debug, World)]",
            "#[world(init = Self::new)]",
            f"pub struct {self._pascal_case(parser.feature_name)}World {{",
            "    // TODO: Add test state fields",
            "    input: Option<TestInput>,",
            "    result: Option<Result<TestOutput, TestError>>,",
            "}",
            "",
            f"impl {self._pascal_case(parser.feature_name)}World {{",
            "    fn new() -> Self {",
            "        Self {",
            "            input: None,",
            "            result: None,",
            "        }",
            "    }",
            "}",
            "",
        ]
        
        # Collect unique steps
        given_steps = set()
        when_steps = set()
        then_steps = set()
        
        for ac in parser.criteria:
            given_steps.update(ac.given)
            when_steps.update(ac.when)
            then_steps.update(ac.then + ac.and_clauses)
        
        # Generate step definitions
        lines.append("// ===== Given Steps =====")
        lines.append("")
        for step in sorted(given_steps):
            lines.extend(self._generate_step("given", step, parser.feature_name))
            lines.append("")
        
        lines.append("// ===== When Steps =====")
        lines.append("")
        for step in sorted(when_steps):
            lines.extend(self._generate_step("when", step, parser.feature_name))
            lines.append("")
        
        lines.append("// ===== Then Steps =====")
        lines.append("")
        for step in sorted(then_steps):
            lines.extend(self._generate_step("then", step, parser.feature_name))
            lines.append("")
        
        # Test runner
        lines.extend([
            "// ===== Test Runner =====",
            "",
            "#[tokio::main]",
            "async fn main() {",
            f'    {self._pascal_case(parser.feature_name)}World::run("tests/features/{parser.feature_name}.feature").await;',
            "}",
        ])
        
        return "\n".join(lines)
    
    def _generate_step(self, step_type: str, step_text: str, feature_name: str) -> List[str]:
        import re
        placeholders = re.findall(r'<(\w+)>', step_text)
        
        # Convert to cucumber-rs pattern
        pattern = re.sub(r'<(\w+)>', r'{string}', step_text)
        
        # Generate function name
        func_name = re.sub(r'[^a-zA-Z0-9]', '_', step_text.lower())[:50]
        
        world_type = f"{self._pascal_case(feature_name)}World"
        
        if placeholders:
            params = ", ".join([f"{p}: String" for p in placeholders])
            lines = [
                f'#[{step_type}(expr = "{pattern}")]',
                f"async fn {func_name}(world: &mut {world_type}, {params}) {{",
                f"    // TODO: Implement step",
                f"    todo!()",
                f"}}",
            ]
        else:
            lines = [
                f'#[{step_type}("{step_text}")]',
                f"async fn {func_name}(world: &mut {world_type}) {{",
                f"    // TODO: Implement step",
                f"    todo!()",
                f"}}",
            ]
        
        return lines
    
    def _pascal_case(self, name: str) -> str:
        return "".join(word.capitalize() for word in name.replace("-", "_").split("_"))


def main():
    parser = argparse.ArgumentParser(
        description="Generate BDD tests from acceptance.yaml"
    )
    parser.add_argument(
        "spec_dir",
        type=Path,
        help="Path to the spec directory containing acceptance.yaml"
    )
    parser.add_argument(
        "--lang",
        choices=["gherkin", "typescript", "go", "rust", "java"],
        default="gherkin",
        help="Target language/framework"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output directory (default: stdout)"
    )
    
    args = parser.parse_args()
    
    if not args.spec_dir.exists():
        print(f"ERROR: Spec directory not found: {args.spec_dir}", file=sys.stderr)
        sys.exit(2)
    
    # Parse acceptance.yaml
    acceptance_parser = AcceptanceParser(args.spec_dir)
    if not acceptance_parser.parse():
        print("ERROR: Failed to parse acceptance.yaml", file=sys.stderr)
        sys.exit(1)
    
    print(f"Parsed {len(acceptance_parser.criteria)} acceptance criteria", file=sys.stderr)
    
    # Generate based on language
    generators = {
        "gherkin": GherkinGenerator(),
        "typescript": TypeScriptGenerator(),
        "go": GinkgoGenerator(),
        "rust": RustGenerator(),
        "java": None,  # Placeholder
    }
    
    generator = generators.get(args.lang)
    if generator is None:
        print(f"ERROR: Language '{args.lang}' not yet implemented", file=sys.stderr)
        sys.exit(1)
    
    output = generator.generate(acceptance_parser)
    
    # Output
    if args.output:
        # Determine filename
        extensions = {
            "gherkin": ".feature",
            "typescript": ".steps.ts",
            "go": "_test.go",
            "rust": ".rs",
        }
        ext = extensions.get(args.lang, ".txt")
        filename = acceptance_parser.feature_name + ext
        
        output_path = args.output / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(output)
        
        print(f"Generated: {output_path}", file=sys.stderr)
    else:
        print(output)
    
    sys.exit(0)


if __name__ == "__main__":
    main()
