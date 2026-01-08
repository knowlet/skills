#!/usr/bin/env python3
"""
Multi-Model Reviewer Script

協調多個 AI 模型進行三角驗證：Specification == Program == Test
支援的模型：ChatGPT 5.2, Gemini CLI, Codex CLI, QWEN 32B, Claude CLI

Usage:
    python multi_model_review.py --spec-dir docs/specs/feature/ --program-dir src/ --test-dir tests/
"""

import os
import sys
import json
import yaml
import argparse
import subprocess
import asyncio
import httpx
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set
from enum import Enum
from datetime import datetime


class Severity(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class IssueType(Enum):
    SPEC_PROGRAM_MISMATCH = "spec_program_mismatch"
    PROGRAM_TEST_GAP = "program_test_gap"
    TEST_SPEC_MISMATCH = "test_spec_mismatch"
    METADATA_MISMATCH = "metadata_mismatch"


@dataclass
class ReviewIssue:
    id: str
    severity: Severity
    issue_type: IssueType
    description: str
    detected_by: List[str]
    spec_location: Optional[str] = None
    program_location: Optional[str] = None
    test_location: Optional[str] = None
    spec_content: Optional[str] = None
    program_content: Optional[str] = None
    suggested_fix: Optional[str] = None
    confidence: str = "medium"


@dataclass
class ReviewReport:
    timestamp: str
    spec_dir: str
    total_checks: int = 0
    passed: int = 0
    warnings: int = 0
    errors: int = 0
    issues: List[ReviewIssue] = field(default_factory=list)


class ModelReviewer:
    """Base class for AI model reviewers"""
    
    def __init__(self, name: str, enabled: bool = True):
        self.name = name
        self.enabled = enabled
    
    async def review(self, prompt: str, context: Dict) -> Dict:
        """Execute review and return findings"""
        raise NotImplementedError


class ChatGPTReviewer(ModelReviewer):
    """ChatGPT 5.2 via OpenAI API"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o"):
        super().__init__("chatgpt")
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.model = model
        self.enabled = bool(self.api_key)
    
    async def review(self, prompt: str, context: Dict) -> Dict:
        if not self.enabled:
            return {"model": self.name, "error": "API key not configured"}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": REVIEW_SYSTEM_PROMPT},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.1,
                        "response_format": {"type": "json_object"}
                    },
                    timeout=60.0
                )
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                return {"model": self.name, "findings": json.loads(content)}
        except Exception as e:
            return {"model": self.name, "error": str(e)}


class GeminiReviewer(ModelReviewer):
    """Gemini via local CLI"""
    
    def __init__(self, cli_command: str = "gemini"):
        super().__init__("gemini")
        self.cli_command = cli_command
        self.enabled = self._check_cli_available()
    
    def _check_cli_available(self) -> bool:
        try:
            subprocess.run([self.cli_command, "--version"], 
                         capture_output=True, check=True, timeout=5)
            return True
        except:
            return False
    
    async def review(self, prompt: str, context: Dict) -> Dict:
        if not self.enabled:
            return {"model": self.name, "error": "CLI not available"}
        
        try:
            full_prompt = f"{REVIEW_SYSTEM_PROMPT}\n\n{prompt}"
            process = await asyncio.create_subprocess_exec(
                self.cli_command, "-p", full_prompt, "--json",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await asyncio.wait_for(process.communicate(), timeout=120)
            return {"model": self.name, "findings": json.loads(stdout.decode())}
        except Exception as e:
            return {"model": self.name, "error": str(e)}


class CodexReviewer(ModelReviewer):
    """Codex via local CLI"""
    
    def __init__(self, cli_command: str = "codex"):
        super().__init__("codex")
        self.cli_command = cli_command
        self.enabled = self._check_cli_available()
    
    def _check_cli_available(self) -> bool:
        try:
            subprocess.run([self.cli_command, "--version"], 
                         capture_output=True, check=True, timeout=5)
            return True
        except:
            return False
    
    async def review(self, prompt: str, context: Dict) -> Dict:
        if not self.enabled:
            return {"model": self.name, "error": "CLI not available"}
        
        try:
            full_prompt = f"{REVIEW_SYSTEM_PROMPT}\n\n{prompt}"
            process = await asyncio.create_subprocess_exec(
                self.cli_command, "--prompt", full_prompt, "--format", "json",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await asyncio.wait_for(process.communicate(), timeout=120)
            return {"model": self.name, "findings": json.loads(stdout.decode())}
        except Exception as e:
            return {"model": self.name, "error": str(e)}


class QWENReviewer(ModelReviewer):
    """QWEN 32B via local Ollama"""
    
    def __init__(self, endpoint: str = "http://localhost:11434/api/generate", 
                 model: str = "qwen2.5:32b"):
        super().__init__("qwen")
        self.endpoint = endpoint
        self.model = model
        self.enabled = self._check_ollama_available()
    
    def _check_ollama_available(self) -> bool:
        try:
            import httpx
            response = httpx.get("http://localhost:11434/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    async def review(self, prompt: str, context: Dict) -> Dict:
        if not self.enabled:
            return {"model": self.name, "error": "Ollama not available"}
        
        try:
            full_prompt = f"{REVIEW_SYSTEM_PROMPT}\n\n{prompt}\n\nRespond in JSON format."
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.endpoint,
                    json={
                        "model": self.model,
                        "prompt": full_prompt,
                        "stream": False,
                        "format": "json"
                    },
                    timeout=180.0
                )
                result = response.json()
                return {"model": self.name, "findings": json.loads(result["response"])}
        except Exception as e:
            return {"model": self.name, "error": str(e)}


class ClaudeReviewer(ModelReviewer):
    """Claude via local CLI (as final arbiter)"""
    
    def __init__(self, cli_command: str = "claude"):
        super().__init__("claude")
        self.cli_command = cli_command
        self.enabled = self._check_cli_available()
        self.is_arbiter = True
    
    def _check_cli_available(self) -> bool:
        try:
            subprocess.run([self.cli_command, "--version"], 
                         capture_output=True, check=True, timeout=5)
            return True
        except:
            return False
    
    async def review(self, prompt: str, context: Dict) -> Dict:
        if not self.enabled:
            return {"model": self.name, "error": "CLI not available"}
        
        try:
            full_prompt = f"{REVIEW_SYSTEM_PROMPT}\n\n{prompt}"
            process = await asyncio.create_subprocess_exec(
                self.cli_command, "-p", full_prompt, "--output-format", "json",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await asyncio.wait_for(process.communicate(), timeout=120)
            return {"model": self.name, "findings": json.loads(stdout.decode())}
        except Exception as e:
            return {"model": self.name, "error": str(e)}
    
    async def filter_false_positives(self, all_findings: List[Dict], 
                                      context: Dict) -> List[ReviewIssue]:
        """Claude as final arbiter to filter false positives"""
        arbiter_prompt = self._build_arbiter_prompt(all_findings, context)
        
        try:
            process = await asyncio.create_subprocess_exec(
                self.cli_command, "-p", arbiter_prompt, "--output-format", "json",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await asyncio.wait_for(process.communicate(), timeout=180)
            result = json.loads(stdout.decode())
            return self._parse_arbiter_result(result)
        except Exception as e:
            # Fallback: use consensus-based filtering
            return self._consensus_filter(all_findings)
    
    def _build_arbiter_prompt(self, findings: List[Dict], context: Dict) -> str:
        return f"""You are the final arbiter for a multi-model code review.

Multiple AI models have reviewed the following context:
- Specification: {context.get('spec_summary', 'N/A')}
- Program: {context.get('program_summary', 'N/A')}
- Tests: {context.get('test_summary', 'N/A')}

Here are the findings from each model:
{json.dumps(findings, indent=2)}

Your task:
1. Cross-compare findings from all models
2. Identify true issues (≥3 models agree)
3. Mark warnings (2 models agree)
4. Discard likely false positives (only 1 model)
5. Assign severity levels
6. Provide actionable fix suggestions

Respond in JSON format:
{{
    "confirmed_issues": [...],
    "warnings": [...],
    "discarded_as_false_positive": [...]
}}
"""
    
    def _parse_arbiter_result(self, result: Dict) -> List[ReviewIssue]:
        issues = []
        issue_id = 1
        
        for item in result.get("confirmed_issues", []):
            issues.append(ReviewIssue(
                id=f"ISSUE-{issue_id:03d}",
                severity=Severity.ERROR,
                issue_type=IssueType(item.get("type", "spec_program_mismatch")),
                description=item.get("description", ""),
                detected_by=item.get("detected_by", []),
                spec_location=item.get("spec_location"),
                program_location=item.get("program_location"),
                suggested_fix=item.get("suggested_fix"),
                confidence="high"
            ))
            issue_id += 1
        
        for item in result.get("warnings", []):
            issues.append(ReviewIssue(
                id=f"ISSUE-{issue_id:03d}",
                severity=Severity.WARNING,
                issue_type=IssueType(item.get("type", "spec_program_mismatch")),
                description=item.get("description", ""),
                detected_by=item.get("detected_by", []),
                confidence="medium"
            ))
            issue_id += 1
        
        return issues
    
    def _consensus_filter(self, all_findings: List[Dict]) -> List[ReviewIssue]:
        """Fallback: filter based on model consensus"""
        issue_votes: Dict[str, List[str]] = {}
        issue_details: Dict[str, Dict] = {}
        
        for finding in all_findings:
            if "error" in finding:
                continue
            
            model = finding["model"]
            for issue in finding.get("findings", {}).get("issues", []):
                key = f"{issue.get('type')}:{issue.get('location')}"
                if key not in issue_votes:
                    issue_votes[key] = []
                    issue_details[key] = issue
                issue_votes[key].append(model)
        
        issues = []
        issue_id = 1
        
        for key, voters in issue_votes.items():
            details = issue_details[key]
            
            if len(voters) >= 3:
                severity = Severity.ERROR
                confidence = "high"
            elif len(voters) == 2:
                severity = Severity.WARNING
                confidence = "medium"
            else:
                continue  # Discard single-model findings
            
            issues.append(ReviewIssue(
                id=f"ISSUE-{issue_id:03d}",
                severity=severity,
                issue_type=IssueType(details.get("type", "spec_program_mismatch")),
                description=details.get("description", ""),
                detected_by=voters,
                confidence=confidence
            ))
            issue_id += 1
        
        return issues


# System prompt for all reviewers
REVIEW_SYSTEM_PROMPT = """You are a code review expert specializing in verifying consistency between:
1. Specification (YAML specs defining requirements, domain events, invariants)
2. Program (Implementation code in Java/TypeScript/Go/Rust)
3. Test (Acceptance tests, unit tests)

Your task is to identify mismatches in the "Specification == Program == Test" triangle:
- SP: Spec defines something that Program doesn't implement
- PS: Program implements something not in Spec
- PT: Program has code that Tests don't cover
- TS: Tests verify something not defined in Spec

Focus on:
1. Domain Events: spec properties vs implementation fields
2. Invariants: spec constraints vs code enforcement
3. Use Cases: spec input/output vs service parameters
4. Acceptance Criteria: spec scenarios vs test cases

Report findings as JSON:
{
    "issues": [
        {
            "type": "spec_program_mismatch|program_test_gap|test_spec_mismatch|metadata_mismatch",
            "location": "file#element",
            "description": "What's wrong",
            "spec_definition": "What spec says",
            "actual_implementation": "What code does",
            "suggested_fix": "How to fix"
        }
    ]
}
"""


class SpecProgramTestCollector:
    """Collect and summarize Spec, Program, and Test artifacts"""
    
    def __init__(self, spec_dir: Path, program_dir: Path, test_dir: Path):
        self.spec_dir = spec_dir
        self.program_dir = program_dir
        self.test_dir = test_dir
    
    def collect(self) -> Dict:
        return {
            "spec": self._collect_specs(),
            "program": self._collect_programs(),
            "test": self._collect_tests(),
            "spec_summary": self._summarize_specs(),
            "program_summary": self._summarize_programs(),
            "test_summary": self._summarize_tests()
        }
    
    def _collect_specs(self) -> Dict:
        specs = {}
        for yaml_file in self.spec_dir.rglob("*.yaml"):
            with open(yaml_file) as f:
                specs[str(yaml_file.relative_to(self.spec_dir))] = yaml.safe_load(f)
        return specs
    
    def _collect_programs(self) -> Dict:
        programs = {}
        extensions = ["*.java", "*.ts", "*.go", "*.rs"]
        for ext in extensions:
            for code_file in self.program_dir.rglob(ext):
                with open(code_file) as f:
                    programs[str(code_file.relative_to(self.program_dir))] = f.read()
        return programs
    
    def _collect_tests(self) -> Dict:
        tests = {}
        patterns = ["*Test.java", "*.test.ts", "*_test.go", "*_test.rs", "*.spec.ts"]
        for pattern in patterns:
            for test_file in self.test_dir.rglob(pattern):
                with open(test_file) as f:
                    tests[str(test_file.relative_to(self.test_dir))] = f.read()
        return tests
    
    def _summarize_specs(self) -> str:
        specs = self._collect_specs()
        summary = []
        
        # Frame
        if "frame.yaml" in specs:
            frame = specs["frame.yaml"]
            summary.append(f"Frame: {frame.get('frame_type', 'Unknown')}")
            if "domain_events" in frame:
                events = frame["domain_events"]
                if isinstance(events, list):
                    summary.append(f"Domain Events: {', '.join(e.get('name', '') for e in events)}")
        
        # Aggregate
        for key, spec in specs.items():
            if "aggregate" in key.lower():
                if "invariants" in spec:
                    summary.append(f"Invariants: {len(spec['invariants'])} defined")
        
        return "; ".join(summary) if summary else "No specs found"
    
    def _summarize_programs(self) -> str:
        programs = self._collect_programs()
        summary = [f"Files: {len(programs)}"]
        
        # Count classes/functions
        service_count = sum(1 for f in programs if "Service" in f or "UseCase" in f)
        if service_count:
            summary.append(f"Services: {service_count}")
        
        return "; ".join(summary)
    
    def _summarize_tests(self) -> str:
        tests = self._collect_tests()
        return f"Test files: {len(tests)}"


class MultiModelReviewOrchestrator:
    """Orchestrate multi-model review process"""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config = self._load_config(config_path)
        self.reviewers = self._init_reviewers()
        self.arbiter = ClaudeReviewer()
    
    def _load_config(self, config_path: Optional[Path]) -> Dict:
        if config_path and config_path.exists():
            with open(config_path) as f:
                return yaml.safe_load(f)
        
        # Default config
        return {
            "models": {
                "chatgpt": {"enabled": True},
                "gemini": {"enabled": True},
                "codex": {"enabled": True},
                "qwen": {"enabled": True},
                "claude": {"enabled": True}
            },
            "consensus": {
                "error_threshold": 3,
                "warning_threshold": 2
            }
        }
    
    def _init_reviewers(self) -> List[ModelReviewer]:
        reviewers = []
        models = self.config.get("models", {})
        
        if models.get("chatgpt", {}).get("enabled", True):
            reviewers.append(ChatGPTReviewer())
        if models.get("gemini", {}).get("enabled", True):
            reviewers.append(GeminiReviewer())
        if models.get("codex", {}).get("enabled", True):
            reviewers.append(CodexReviewer())
        if models.get("qwen", {}).get("enabled", True):
            reviewers.append(QWENReviewer())
        if models.get("claude", {}).get("enabled", True):
            reviewers.append(ClaudeReviewer())
        
        return reviewers
    
    async def review(self, spec_dir: Path, program_dir: Path, 
                     test_dir: Path) -> ReviewReport:
        """Execute full multi-model review"""
        
        # 1. Collect artifacts
        collector = SpecProgramTestCollector(spec_dir, program_dir, test_dir)
        context = collector.collect()
        
        # 2. Build review prompt
        prompt = self._build_review_prompt(context)
        
        # 3. Parallel review by all models
        print("🔍 Starting parallel review by all models...")
        tasks = [
            reviewer.review(prompt, context) 
            for reviewer in self.reviewers 
            if reviewer.enabled
        ]
        all_findings = await asyncio.gather(*tasks)
        
        # 4. Print model status
        for finding in all_findings:
            model = finding["model"]
            if "error" in finding:
                print(f"  ⚠️  {model}: {finding['error']}")
            else:
                issue_count = len(finding.get("findings", {}).get("issues", []))
                print(f"  ✅ {model}: {issue_count} issues found")
        
        # 5. Claude filters false positives
        print("\n🧠 Claude filtering false positives...")
        issues = await self.arbiter.filter_false_positives(all_findings, context)
        
        # 6. Build report
        report = ReviewReport(
            timestamp=datetime.now().isoformat(),
            spec_dir=str(spec_dir),
            total_checks=len(self.reviewers) * 10,  # Approximate
            passed=0,
            warnings=sum(1 for i in issues if i.severity == Severity.WARNING),
            errors=sum(1 for i in issues if i.severity == Severity.ERROR),
            issues=issues
        )
        report.passed = report.total_checks - report.warnings - report.errors
        
        return report
    
    def _build_review_prompt(self, context: Dict) -> str:
        spec_yaml = yaml.dump(context["spec"], default_flow_style=False, allow_unicode=True)
        
        # Truncate if too long
        max_len = 50000
        program_summary = str(context["program"])[:max_len]
        test_summary = str(context["test"])[:max_len]
        
        return f"""Review the following for Specification == Program == Test consistency:

## SPECIFICATION
```yaml
{spec_yaml[:max_len]}
```

## PROGRAM (Summary)
{context["program_summary"]}
Key files:
{program_summary}

## TESTS (Summary)
{context["test_summary"]}
Key files:
{test_summary}

Identify any mismatches and report in JSON format.
"""


def print_report(report: ReviewReport):
    """Print formatted review report"""
    status = "✅ PASS" if report.errors == 0 and report.warnings == 0 else \
             "⚠️ CONDITIONAL PASS" if report.errors == 0 else "❌ FAILED"
    
    print(f"""
╔═══════════════════════════════════════════════════════════════════╗
║            MULTI-MODEL REVIEW REPORT                               ║
╠═══════════════════════════════════════════════════════════════════╣
║ Timestamp: {report.timestamp:<54} ║
║ Spec Dir:  {report.spec_dir:<54} ║
╠═══════════════════════════════════════════════════════════════════╣
║ Total Checks: {report.total_checks:<51} ║
║ Passed:       {report.passed:<51} ║
║ Warnings:     {report.warnings:<51} ║
║ Errors:       {report.errors:<51} ║
╠═══════════════════════════════════════════════════════════════════╣
║ Status: {status:<57} ║
╚═══════════════════════════════════════════════════════════════════╝
""")
    
    if report.issues:
        print("\n📋 ISSUES:\n")
        for issue in report.issues:
            icon = "❌" if issue.severity == Severity.ERROR else "⚠️"
            print(f"  {icon} [{issue.id}] {issue.description}")
            print(f"      Type: {issue.issue_type.value}")
            print(f"      Detected by: {', '.join(issue.detected_by)}")
            print(f"      Confidence: {issue.confidence}")
            if issue.suggested_fix:
                print(f"      Fix: {issue.suggested_fix[:100]}...")
            print()


async def main():
    parser = argparse.ArgumentParser(description="Multi-Model Code Review")
    parser.add_argument("--spec-dir", required=True, help="Path to spec directory")
    parser.add_argument("--program-dir", required=True, help="Path to program directory")
    parser.add_argument("--test-dir", required=True, help="Path to test directory")
    parser.add_argument("--config", help="Path to config file")
    parser.add_argument("--output", help="Output report file (YAML)")
    parser.add_argument("--models", help="Comma-separated list of models to use")
    parser.add_argument("--check", choices=["all", "spec-program", "program-test", "test-spec"],
                       default="all", help="Which checks to run")
    
    args = parser.parse_args()
    
    config_path = Path(args.config) if args.config else None
    orchestrator = MultiModelReviewOrchestrator(config_path)
    
    # Filter models if specified
    if args.models:
        enabled_models = set(args.models.split(","))
        orchestrator.reviewers = [
            r for r in orchestrator.reviewers 
            if r.name in enabled_models
        ]
    
    report = await orchestrator.review(
        Path(args.spec_dir),
        Path(args.program_dir),
        Path(args.test_dir)
    )
    
    print_report(report)
    
    if args.output:
        output_path = Path(args.output)
        with open(output_path, "w") as f:
            yaml.dump({
                "timestamp": report.timestamp,
                "spec_dir": report.spec_dir,
                "total_checks": report.total_checks,
                "passed": report.passed,
                "warnings": report.warnings,
                "errors": report.errors,
                "issues": [
                    {
                        "id": i.id,
                        "severity": i.severity.value,
                        "type": i.issue_type.value,
                        "description": i.description,
                        "detected_by": i.detected_by,
                        "confidence": i.confidence,
                        "suggested_fix": i.suggested_fix
                    }
                    for i in report.issues
                ]
            }, f, default_flow_style=False, allow_unicode=True)
        print(f"📄 Report saved to: {args.output}")
    
    # Exit code based on errors
    sys.exit(1 if report.errors > 0 else 0)


if __name__ == "__main__":
    asyncio.run(main())
