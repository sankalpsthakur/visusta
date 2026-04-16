#!/usr/bin/env python3
"""
VISUSTA — Gap Analysis Auditor

Purpose
-------
Automated audit of the current reporting artifacts to detect:
- Wrong-jurisdiction references (e.g., "Hamburg Township" vs Hamburg, Germany)
- Missing required topic coverage (GHG, Packaging, Water, Waste, Social/Human Rights)
- Cross-jurisdiction regulations in EU/DE scope screening datasets
- Non-actionable references (no URLs / no primary sources signals)
- Non-data-driven PDF builders (hardcoded narrative instead of changelog-driven)

This script is intentionally conservative: it flags potential issues for review.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from config import get_config


REPO_ROOT = Path(__file__).resolve().parent
REG_DATA = REPO_ROOT / "regulatory_data"

_cfg = get_config()

# Required topics and allowed country codes sourced from config/visusta.yaml.
# Extend via config when adding geographies or topics.
REQUIRED_TOPICS = _cfg.screening.required_topics
ALLOWED_COUNTRY_CODES = set(_cfg.screening.allowed_countries)


@dataclass
class Finding:
    severity: str  # "CRITICAL" | "HIGH" | "MEDIUM" | "LOW"
    category: str
    location: str
    message: str
    evidence: Optional[str] = None
    gap_type: str = "regulatory"  # "regulatory" | "data_quality" | "code_health"


# Categories that are code / build-health issues, not compliance gaps.
_CODE_HEALTH_CATEGORIES = frozenset({
    "Reference Parsing",
    "References",
    "Missing File",
    "Non Data-driven Report",
    "Non-actionable Reference",
    "Primary Sources Missing",
})

# Categories that indicate a data-quality gap (missing/incomplete records).
_DATA_QUALITY_CATEGORIES = frozenset({
    "Missing Applicability",
    "Missing Topic Coverage",
    "Missing Data",
})


def _classify_gap_type(category: str) -> str:
    if category in _CODE_HEALTH_CATEGORIES:
        return "code_health"
    if category in _DATA_QUALITY_CATEGORIES:
        return "data_quality"
    return "regulatory"


@dataclass
class AuditReport:
    findings: List[Finding] = field(default_factory=list)

    def add(
        self,
        severity: str,
        category: str,
        location: str,
        message: str,
        evidence: Optional[str] = None,
    ) -> None:
        self.findings.append(
            Finding(
                severity=severity,
                category=category,
                location=location,
                message=message,
                evidence=evidence,
                gap_type=_classify_gap_type(category),
            )
        )

    def to_markdown(self) -> str:
        sev_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        findings = sorted(
            self.findings, key=lambda f: (sev_order.get(f.severity, 9), f.category, f.location)
        )

        lines = [
            "# VISUSTA — Gap Analysis Report",
            "",
            "Scope: EU & Germany sustainability frameworks for food manufacturers.",
            "",
            f"Total findings: {len(findings)}",
            "",
        ]

        if not findings:
            lines.append("No issues detected by automated checks.")
            return "\n".join(lines)

        for f in findings:
            lines.append(f"## {f.severity}: {f.category}")
            lines.append(f"- Location: `{f.location}`")
            lines.append(f"- Issue: {f.message}")
            if f.evidence:
                lines.append(f"- Evidence: `{f.evidence}`")
            lines.append("")

        return "\n".join(lines).rstrip() + "\n"


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _load_json(path: Path) -> Any:
    return json.loads(_read_text(path))


def _extract_refs_from_build_script(script_path: Path) -> Tuple[List[str], List[str]]:
    """
    Heuristic extraction of `refs = [...]` from the ReportLab builders.
    Returns (refs, parse_warnings).
    """
    text = _read_text(script_path)
    warnings: List[str] = []

    # Find the first "refs = [" in the file.
    m = re.search(r"^\s*refs\s*=\s*\[\s*$", text, flags=re.MULTILINE)
    if not m:
        return [], [f"Could not find `refs = [` block in {script_path.name}"]

    start = m.end()
    # Slice from start to the first line containing "]." at same indent OR "for ref in refs:"
    # We'll stop at the first standalone closing bracket line.
    rest = text[start:]
    end_m = re.search(r"^\s*\]\s*$", rest, flags=re.MULTILINE)
    if not end_m:
        return [], [f"Could not find end of `refs` list in {script_path.name}"]

    block = rest[: end_m.start()]
    refs: List[str] = []

    for line in block.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("#"):
            continue
        # Expect Python string literal lines like: '[1] "Title," Publisher.',
        str_m = re.match(
            r"^[rRuUbBfF]*(?P<q>['\"])(?P<content>.*?)(?P=q)\s*,?\s*$",
            line,
        )
        if not str_m:
            # tolerate trailing + or multiline formatting; just record a warning
            warnings.append(f"Unparsed ref line: {line[:120]}")
            continue
        refs.append(str_m.group("content"))

    return refs, warnings


def _looks_like_has_url(ref: str) -> bool:
    return "http://" in ref or "https://" in ref or "www." in ref


def _audit_references(report: AuditReport, script_path: Path, refs: List[str]) -> None:
    location = str(script_path.relative_to(REPO_ROOT))
    if not refs:
        report.add(
            "CRITICAL",
            "References",
            location,
            "No references extracted; report cannot be validated against sources.",
        )
        return

    suspicious_patterns = [
        (re.compile(r"\bHamburg Township\b", re.IGNORECASE), "Hamburg Township (US)"),
        (re.compile(r"\brevize\b", re.IGNORECASE), "revize.com (municipal CMS often US)"),
        (re.compile(r"\bhamburgmi\b", re.IGNORECASE), "hamburgmi (Michigan)"),
        (re.compile(r"\busgovcloudapi\b", re.IGNORECASE), "usgovcloudapi (US Gov cloud)"),
        (re.compile(r"\bMichigan\b", re.IGNORECASE), "Michigan"),
        (re.compile(r"\bTownship\b", re.IGNORECASE), "Township (usually US local gov)"),
    ]

    for ref in refs:
        # 1) Wrong-jurisdiction red flags
        for rx, label in suspicious_patterns:
            if rx.search(ref):
                report.add(
                    "CRITICAL",
                    "Wrong Jurisdiction",
                    location,
                    "Reference strongly suggests a non-DE/EU jurisdiction, risking incorrect conclusions.",
                    evidence=f"{label}: {ref}",
                )
                break

        # 2) Non-actionable references: no URL
        if not _looks_like_has_url(ref):
            report.add(
                "HIGH",
                "Non-actionable Reference",
                location,
                "Reference does not include a URL; cannot be independently verified in an audit.",
                evidence=ref,
            )

    # 3) Sanity check: for EU/DE scope, at least one primary source is expected
    # This is a heuristic check on publisher strings.
    primary_signals = ("EUR-Lex", "Bundesgesetzblatt", "Bundestag", "Bürgerschaft", "Hamburg.de")
    if not any(any(sig.lower() in r.lower() for sig in primary_signals) for r in refs):
        report.add(
            "HIGH",
            "Primary Sources Missing",
            location,
            "No obvious primary-source signals found (e.g., EUR-Lex, Bundesgesetzblatt, parliament gazettes).",
        )


def _audit_monthly_topic_coverage(report: AuditReport, state_path: Path) -> None:
    location = str(state_path.relative_to(REPO_ROOT))
    state = _load_json(state_path)
    covered = state.get("topics_covered") or []
    missing = [t for t in REQUIRED_TOPICS if t not in covered]
    if missing:
        report.add(
            "CRITICAL",
            "Missing Topic Coverage",
            location,
            "Monthly screening does not cover all required topics (must always report per topic, even if 'no change').",
            evidence=f"missing={missing}, covered={covered}",
        )


def _audit_cross_jurisdiction_regulations(report: AuditReport, state_path: Path) -> None:
    location = str(state_path.relative_to(REPO_ROOT))
    state = _load_json(state_path)
    regs = state.get("regulations") or []
    for reg in regs:
        rid = str(reg.get("regulation_id") or "")
        applicable = set(reg.get("applicable_countries") or [])
        if not applicable:
            report.add(
                "MEDIUM",
                "Missing Applicability",
                location,
                "Regulation entry missing `applicable_countries`; scope filtering and audit are weakened.",
                evidence=rid,
            )
            continue

        if not applicable.issubset(ALLOWED_COUNTRY_CODES):
            report.add(
                "CRITICAL",
                "Cross-jurisdiction Regulation",
                location,
                "Regulation appears outside EU/DE scope but is included in screening inputs.",
                evidence=f"{rid} applicable_countries={sorted(applicable)}",
            )


def _audit_pdf_builders_are_data_driven(report: AuditReport) -> None:
    """
    Current PDF builders are hardcoded narratives. For the desired workflow, monthly should be a
    technical per-topic change screening driven from changelog JSON.
    """
    builders = [
        REPO_ROOT / "build_monthly_report.py",
        REPO_ROOT / "build_quarterly_brief.py",
    ]
    for p in builders:
        if not p.exists():
            continue
        text = _read_text(p)
        location = str(p.relative_to(REPO_ROOT))

        reads_json = bool(re.search(r"json\\.load|json\\.loads|\\.json", text))
        references_reg_data = "regulatory_data" in text
        if not reads_json and not references_reg_data:
            report.add(
                "HIGH",
                "Non Data-driven Report",
                location,
                "PDF builder appears hardcoded and not generated from the monthly change log / screening state.",
                evidence="No JSON/regulatory_data reads detected",
            )


def _audit_scope(client_id: Optional[str]) -> Tuple[Path, Path]:
    if client_id:
        scoped_root = REG_DATA / client_id
        return scoped_root / "states", scoped_root / "audits"
    return REG_DATA / "states", REG_DATA / "audits"


def run_audit(client_id: Optional[str] = None) -> AuditReport:
    report = AuditReport()
    states_dir, out_dir = _audit_scope(client_id)

    # 1) Audit report references embedded in PDF builders
    for script in [REPO_ROOT / "build_monthly_report.py", REPO_ROOT / "build_quarterly_brief.py"]:
        if not script.exists():
            report.add("MEDIUM", "Missing File", str(script), "Expected builder script missing.")
            continue
        refs, warnings = _extract_refs_from_build_script(script)
        for w in warnings:
            report.add("LOW", "Reference Parsing", str(script.relative_to(REPO_ROOT)), w)
        _audit_references(report, script, refs)

    # 2) Audit screening state topic coverage and jurisdiction correctness
    if not states_dir.exists():
        report.add("CRITICAL", "Missing Data", str(states_dir), "No screening states directory found.")
    else:
        state_files = sorted(states_dir.glob("*.json"))
        if not state_files:
            report.add("CRITICAL", "Missing Data", str(states_dir), "No state JSON files found.")
        for sf in state_files:
            _audit_monthly_topic_coverage(report, sf)
            _audit_cross_jurisdiction_regulations(report, sf)

    # 3) Check whether the builders are data-driven vs changelog-driven
    _audit_pdf_builders_are_data_driven(report)

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "gap_analysis_report.md"
    out_path.write_text(report.to_markdown(), encoding="utf-8")

    return report


def main() -> None:
    report = run_audit()
    out_path = _audit_scope(None)[1] / "gap_analysis_report.md"

    print(report.to_markdown())
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
