# Source of Truth — Precedence Order

When documents disagree, resolve conflicts in this order. Higher = wins.

## Precedence (highest → lowest)

1. **`docs/theory/five_layer_capital_stack.md`** — Canonical V5 framing. All layer definitions, ordering, and mechanism claims derive from here.
2. **`docs/FACTS.md`** — Canonical numeric values. Any quoted figure in any other document must match a key here.
3. **V5 Atlas Reframe PDF** (`v5_atlas_reframe_capital_stack_theory.pdf` in Space) — Original reframe source; used only when `five_layer_capital_stack.md` is silent on a point.
4. **Below the Line — Chapter Outlines.docx** — Chapter structure, narrative order, thesis argument flow.
5. **Notion main thesis page** (`32fe9d46-2089-81df-bd6c-e2a13cfc7e44`) — Writing and draft work. Must reflect items 1–4; never the reverse.
6. **Atlas Progress Log (Notion)** — Running execution log. Time-ordered; never used to override an upstream claim.

## Resolution rules

- If README contradicts `FACTS.md` → README is wrong; fix README.
- If a chapter draft contradicts `five_layer_capital_stack.md` → draft is wrong; fix draft.
- If Notion contradicts a repo doc → Notion is wrong; fix Notion.
- If a new empirical finding changes a canonical fact → update `FACTS.md` **first** in a PR, then propagate to all downstream docs in the same PR.

## When you must escalate

- Disagreement between `five_layer_capital_stack.md` and a chapter draft about what a layer *means* (not just its number): open an issue labeled `theory-conflict`, stop writing until resolved.
- Disagreement between two sources both at the same precedence level: resolve by date — newer wins — and document the supersession in the commit message.

## Forbidden

- Storing authoritative numeric facts in Notion, Google Docs, or PPTX files. Those are derivative surfaces.
- Copying numbers into READMEs/chapters without a `FACTS.md` key comment (e.g., `$369.2M <!-- FACTS:L5_NORTH_TOTAL -->`) — the CI check relies on these.
- Long-lived feature branches. See `CONTRIBUTING.md`.
