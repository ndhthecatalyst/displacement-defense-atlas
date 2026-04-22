# Contributing to Displacement Defense Atlas

This repo supports Nicholas D. Hawkins's TSU Freeman Honors undergraduate thesis (*Below the Line*, due December 15, 2027). Contribution rules exist to prevent the kind of branch divergence that triggered PR #1 and PR #2.

## Branching rules

1. **`main` is the only long-lived branch.** Everything else is a short-lived feature branch.
2. **No feature branch may live more than 7 days without rebasing onto `main`.** If a branch is older than a week, either rebase + force-push-with-lease *to your own feature branch* (never to main) or abandon and re-cut from fresh main.
3. **All changes reach `main` via pull request.** Direct pushes to `main` are blocked by branch protection.
4. **At least one approving review required** before merging to `main`.
5. **Linear history required on `main`.** No merge commits; rebase or squash-merge only.
6. **No force-pushes to `main`.** Ever.

## Single source of truth

See `docs/SOURCE_OF_TRUTH.md` for the precedence order. The short version:

1. `docs/theory/five_layer_capital_stack.md` = canonical theory
2. `docs/FACTS.md` = canonical numbers
3. Everything else (README, variable_dictionary.md, chapter drafts, Notion) is downstream.

**If you change a canonical number, you change `docs/FACTS.md` first, in the same PR that propagates the change to downstream docs.** CI will fail otherwise.

## Commit & PR conventions

- **Commit messages** use Conventional Commits: `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `data:`, `theory:`.
- **PR titles** should describe the end-state, not the diff. Good: "H4 Readiness: rebased onto post-V5 main". Bad: "update files".
- **PR bodies** must state (a) what changed, (b) which canonical docs were touched, (c) whether any `FACTS.md` keys moved.

## Data layer conventions

- Raw data → `data/raw/<layer>_<name>/`. V5 target naming: `layer1_cip`, `layer2_pid`, `layer3_tif_oz`, `layer4_sfr`, `layer5_vendor_residue`. V4 directory names (`layer1_investment`, `layer2_mechanism`, `layer3_early_warning`, `layer4_readiness`) remain in place until Chapter 4 stabilizes, then renamed in a single dedicated PR.
- Derived outputs → `outputs/`
- Scripts → `scripts/analysis/<hypothesis>/` for H1–H6 analysis work; `scripts/` top-level only for utility scripts.
- Maps → `maps/<hypothesis>/`

## Theory changes

Any change to the five-layer structure (adding/removing a layer, reordering, redefining) **must start** in `docs/theory/five_layer_capital_stack.md` and cascade outward in the same PR.

## CI checks

The `docs-consistency` workflow runs on every PR. It greps README.md, `docs/variable_dictionary.md`, and `docs/theory/five_layer_capital_stack.md` for canonical values and fails if any drift from `docs/FACTS.md`. To add a new canonical value, add it to `FACTS.md` first, then reference it.

## Questions

Open an issue labeled `question`. For theory conflicts, label `theory-conflict` — these block writing until resolved.
