"""Validated claim and ledger data structures."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


STRENGTHS = ("fact", "methodological", "exploratory", "descriptive",
             "hypothesis", "forbidden")
STRENGTH_RANK = {name: rank for rank, name in enumerate(STRENGTHS)}
DIRECTIONS = ("increase", "decrease", "positive", "negative", "mixed",
              "null", "none")


@dataclass
class Claim:
    claim_id: str
    claim_type: str
    canonical_text: str
    source: str
    numbers: dict[str, Any] = field(default_factory=dict)
    direction: str = "none"
    allowed_strength: str = "fact"
    risk_tags: list[str] = field(default_factory=list)
    status: str = "supported"
    notes: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.claim_id or not self.source:
            raise ValueError("claim_id and source are required")
        if self.direction not in DIRECTIONS:
            raise ValueError(f"unsupported direction: {self.direction}")
        if self.allowed_strength not in STRENGTHS:
            raise ValueError(f"unsupported strength: {self.allowed_strength}")

    def downgrade(self, target: str, reason: str) -> None:
        """Apply a monotone policy action; a claim can never be strengthened."""
        if target not in STRENGTHS:
            raise ValueError(f"unsupported strength: {target}")
        if STRENGTH_RANK[target] >= STRENGTH_RANK[self.allowed_strength]:
            self.allowed_strength = target
            self.status = "forbidden" if target == "forbidden" else "downgraded"
            if reason and reason not in self.notes:
                self.notes.append(reason)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ClaimLedger:
    def __init__(self, record_id: str):
        self.record_id = record_id
        self._claims: dict[str, Claim] = {}

    def add(self, claim: Claim) -> None:
        if claim.claim_id in self._claims:
            raise ValueError(f"duplicate claim_id: {claim.claim_id}")
        self._claims[claim.claim_id] = claim

    def all(self) -> list[Claim]:
        return list(self._claims.values())

    def active(self) -> list[Claim]:
        return [claim for claim in self.all()
                if claim.allowed_strength != "forbidden"]

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "n_claims": len(self._claims),
            "claims": [claim.to_dict() for claim in self.all()],
        }
