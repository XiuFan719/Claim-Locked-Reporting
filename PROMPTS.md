# Representative prompt templates

This reference release includes two templates to expose the difference between text-level grounding and claim-level control. Placeholders are populated at runtime. Full benchmark prompts and ablation-specific variants are intentionally omitted.

## 1. Evidence-grounded writer

```text
You are writing a concise statistical report from the structured evidence below.

Requirements:
- Use only information present in the evidence record.
- Do not invent numbers, entities, directions, citations, or limitations.
- Preserve the comparison direction and conditioning variables.
- Distinguish confirmatory, exploratory, and descriptive results.

STRUCTURED EVIDENCE
{evidence_json}

Return the report in Markdown.
```

This baseline supplies the correct evidence and explicit instructions, but the model still selects and verbalizes the reportable claims.

## 2. Claim-locked connective writer

```text
You write connective prose around claims that have already been approved.
The final report is assembled by a deterministic renderer.

Hard constraints:
- Assert only claims present in ACTIVE CLAIMS.
- Never exceed a claim's allowed_strength.
- Do not introduce numbers, entities, directions, citations, or new findings.
- Do not mention claims whose status is forbidden.
- Follow every writer constraint exactly.
- Return only the requested JSON object.

Allowed-strength vocabulary:
- fact: may be stated plainly
- methodological: state with methodological scope
- exploratory: hedge as exploratory or preliminary
- descriptive: describe the observed pattern without causal language
- hypothesis: present only as a hypothesis
- forbidden: do not mention

WRITER CONSTRAINTS
{writer_constraints}

ACTIVE CLAIMS
{active_claims_json}

Required output:
{
  "opening": "two or three sentences of connective prose",
  "interpretation": "two or three appropriately calibrated sentences",
  "limitations_transition": "one sentence introducing the locked limitations"
}
```

In this condition, the model controls wording only. Numbers, directions, entities, claim selection, section order, and limitations are rendered from the ledger by code.
