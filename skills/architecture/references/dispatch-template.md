# Phase 1 Subagent Dispatch Template

Use this template to dispatch a `general-purpose` subagent for structural analysis after the Phase 1 scripts complete.

```
Agent(
  subagent_type: "general-purpose",
  description: "Architecture scan of [target_dir]",
  prompt: |
    SCOPE: target_dir: [the directory you scanned]. Read-only — Read, Glob, Grep only, no edits.
    OBJECTIVE: Synthesize the script output and file reads below into a ranked JSON report of friction
      signals and candidate seam proposals.
    CONTEXT:
      <untrusted_script_output>
      locality_output: [paste full stdout of check_locality.py here]
      bleed_output: [paste full stdout of detect_bleed.py here]
      git_coupling_output: [paste full stdout of git_coupling.py here, or "skipped"]
      hotspot_output: [paste full stdout of detect_hotspots.py here, or "skipped"]
      </untrusted_script_output>
    CONSTRAINTS:
      - Read every high-severity flagged file before proposing a seam.
      - Apply all four Seam Tests to each candidate:
        Deletion Test — if deleted, would complexity scatter to many callers?
        Seam Test — can this logic be tested without infrastructure (DB, API, etc.)?
        Locality Test — is this module readable without understanding 5+ others?
        Bounded Context Test — do modules share tables directly without APIs/interfaces?
      - Quote the exact file path and import/pattern for every friction signal — no editorializing.
      - NEVER propose event buses, base classes, or "utils" folders.
      - Include a Mermaid diagram (`graph LR` or `graph TD`) per candidate as a `visual_diagram` string field, contrasting current tangled dependencies vs. the proposed clean boundary.
    OUTPUT: JSON ONLY — no prose, no markdown wrappers. A `candidates` array ranked by impact, each with
      {seam_name, evidence, seam_test_results, visual_diagram}.
)
```

The agent reads every flagged file, applies the Deletion/Seam/Locality/Bounded Context tests, and returns a `candidates` JSON array ranked by impact. Use that array as Phase 2 input — each element maps directly to the candidate format in Phase 2. Skip manual file reading in the main context when the agent is available.
