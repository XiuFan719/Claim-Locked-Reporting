"""Observable claim builder, auditor, policy controller, and renderer."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .model import Claim, ClaimLedger


RISK_POLICIES = {
    "post_selection": (
        "hypothesis",
        "The result follows data-dependent selection and must remain hypothesis-generating.",
        "Describe post-selection results only as hypotheses.",
    ),
    "incomplete_context": (
        "descriptive",
        "Required contextual information is unavailable; restrict interpretation to description.",
        "Do not infer a mechanism when contextual information is incomplete.",
    ),
    "unsupported_interpretation": (
        "forbidden",
        "The interpretation is not supported by the structured evidence.",
        "Do not render unsupported interpretations.",
    ),
}


def build_ledger(evidence: dict[str, Any]) -> ClaimLedger:
    """Convert a deliberately small public evidence contract into claims."""
    record_id = evidence.get("record_id")
    if not record_id:
        raise ValueError("evidence.record_id is required")
    ledger = ClaimLedger(record_id)
    for item in evidence.get("claims", []):
        ledger.add(Claim(
            claim_id=item["claim_id"],
            claim_type=item["claim_type"],
            canonical_text=item["canonical_text"],
            source=item["source"],
            numbers=item.get("numbers", {}),
            direction=item.get("direction", "none"),
            allowed_strength=item.get("allowed_strength", "fact"),
            risk_tags=list(item.get("risk_tags", [])),
        ))
    return ledger


def audit_ledger(ledger: ClaimLedger, evidence: dict[str, Any]) -> dict[str, Any]:
    """Read-only audit: map fixed triggers to proposed policy actions."""
    available_sources = set(evidence.get("available_sources", []))
    items = []
    for claim in ledger.all():
        if claim.source not in available_sources:
            target = "forbidden"
            reason = f"Evidence source is unavailable: {claim.source}"
            constraints = ["Do not render claims with missing provenance."]
            risks = sorted(set(claim.risk_tags + ["missing_provenance"]))
        else:
            target = claim.allowed_strength
            reasons = []
            constraints = []
            risks = sorted(set(claim.risk_tags))
            for tag in risks:
                policy = RISK_POLICIES.get(tag)
                if not policy:
                    continue
                candidate, policy_reason, constraint = policy
                from .model import STRENGTH_RANK
                if STRENGTH_RANK[candidate] > STRENGTH_RANK[target]:
                    target = candidate
                reasons.append(policy_reason)
                constraints.append(constraint)
            reason = " ".join(reasons) or "No predefined risk triggered."
        items.append({
            "claim_id": claim.claim_id,
            "risk_tags": risks,
            "proposed_strength": target,
            "reason": reason,
            "writer_constraints": sorted(set(constraints)),
        })
    return {"record_id": ledger.record_id, "items": items}


def apply_policy(ledger: ClaimLedger, audit: dict[str, Any]) -> dict[str, Any]:
    """Apply audit decisions and preserve a replayable before/after trace."""
    by_id = {item["claim_id"]: item for item in audit["items"]}
    decisions = []
    constraints = set()
    for claim in ledger.all():
        item = by_id[claim.claim_id]
        before = claim.allowed_strength
        claim.downgrade(item["proposed_strength"], item["reason"])
        constraints.update(item["writer_constraints"])
        decisions.append({
            "claim_id": claim.claim_id,
            "before_strength": before,
            "after_strength": claim.allowed_strength,
            "status": claim.status,
            "reason": item["reason"],
        })
    return {
        "record_id": ledger.record_id,
        "writer_constraints": sorted(constraints),
        "decisions": decisions,
    }


def _format_numbers(numbers: dict[str, Any]) -> str:
    return ", ".join(f"{key}={value}" for key, value in numbers.items()) or "none"


def render_report(ledger: ClaimLedger, connective: dict[str, str]) -> str:
    """Render evidence-bearing fields deterministically.

    The demo accepts optional connective wording, but rejects digits so prose
    cannot become a second numerical channel.
    """
    for key, paragraph in connective.items():
        if re.search(r"\d", paragraph):
            raise ValueError(f"connective prose field {key!r} contains a digit")

    lines = [f"# Claim-Locked Report — {ledger.record_id}", ""]
    if connective.get("opening"):
        lines.extend([connective["opening"], ""])
    lines.extend(["## Locked claims", ""])
    for claim in ledger.active():
        lines.extend([
            f"### {claim.claim_id}", "",
            claim.canonical_text, "",
            f"- Provenance: `{claim.source}`",
            f"- Direction: `{claim.direction}`",
            f"- Numbers: `{_format_numbers(claim.numbers)}`",
            f"- Maximum language strength: `{claim.allowed_strength}`",
            "",
        ])
    if connective.get("interpretation"):
        lines.extend(["## Bounded interpretation", "",
                      connective["interpretation"], ""])
    limitations = [c for c in ledger.active() if c.claim_type == "limitation"]
    if limitations:
        lines.extend(["## Limitations", ""])
        if connective.get("limitations_transition"):
            lines.extend([connective["limitations_transition"], ""])
        lines.extend(f"- {claim.canonical_text}" for claim in limitations)
        lines.append("")
    lines.extend(["---", "",
                  "Evidence-bearing fields above were rendered from the ledger. ",
                  "Connective prose, when present, was supplied separately."])
    return "\n".join(lines)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def run_pipeline(evidence_path: str | Path, connective_path: str | Path,
                 output_dir: str | Path) -> dict[str, Path]:
    evidence = json.loads(Path(evidence_path).read_text())
    connective = json.loads(Path(connective_path).read_text())
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    ledger = build_ledger(evidence)
    _write_json(output / "claim_ledger.json", ledger.to_dict())
    audit = audit_ledger(ledger, evidence)
    _write_json(output / "claim_audit.json", audit)
    trace = apply_policy(ledger, audit)
    _write_json(output / "policy_trace.json", trace)
    _write_json(output / "claim_ledger.final.json", ledger.to_dict())
    (output / "report.md").write_text(render_report(ledger, connective) + "\n")
    return {name: output / name for name in (
        "claim_ledger.json", "claim_audit.json", "policy_trace.json",
        "claim_ledger.final.json", "report.md")}
