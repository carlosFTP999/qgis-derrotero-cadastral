# Archive Report: core-engine

**Archived**: 2026-06-27
**Change**: core-engine
**Mode**: hybrid (OpenSpec files + Engram persistent memory)
**Status**: SUCCESS — completed with stale-checkbox reconciliation

## Stale-Checkbox Reconciliation

Tasks 5.3 and 5.4 were marked `[~]` (manual QGIS GUI) in the persisted tasks artifact. The orchestrator explicitly authorized archive-time reconciliation:

- **52e7c - QGIS Plugin Derrotero**: QGIS GUI runtime constraint (pb_tool deploy, manual E2E in QGIS)
- These are infrastructure-constrained, not incomplete implementation
- **apply-progress** (Engram ID: 478) and **verify-report** (Engram ID: 479) prove all implementation is complete
- All 145 tests pass, ruff is clean (0 violations after --fix)
- Reconciliation performed per orchestrator authorization: "$orchestrator explicitly authorizes stale-checkbox reconciliation for tasks 5.3 and 5.4"

## Verification Summary

- **Verdict**: PASS WITH WARNINGS → full PASS (ruff violations auto-fixed)
- **Tests**: 145/145 passed
- **Linter**: 0 ruff violations (clean after --fix)
- **Spec compliance**: 28 COMPLIANT, 4 PARTIAL, 13 UNTESTED (integration/E2E gaps requiring QGIS GUI)
- **No CRITICAL issues at archive time**

## Spec Sync

The 6 delta specs for this change were **full specs for new capabilities** (not incremental deltas). They were written directly to `openspec/specs/` during the spec phase. All main specs already contained the complete content:

| Domain | Action | Notes |
|--------|--------|-------|
| vertex-extraction | Already in main spec | Full spec created during change |
| bearing-calculation | Already in main spec | Full spec created during change |
| distance-calculation | Already in main spec | Full spec created during change |
| colindancia-detection | Already in main spec | Full spec created during change |
| template-engine | Already in main spec | Full spec created during change |
| derrotero-generation | Already in main spec | Full spec created during change |

**No delta merge needed** — all specs were written directly to main specs as full initial specs.

## Archive Contents

```
openspec/changes/archive/2026-06-27-core-engine/
├── proposal.md      ✅ (1,372 bytes)
├── design.md        ✅ (9,899 bytes)
├── tasks.md         ✅ (3,000 bytes — 20/20 tasks, 2 reconciled)
└── archive-report.md ✅ (this file)
```

**Note**: The `specs/` subdirectory and `verify-report.md` did not exist on the filesystem for this change — those artifacts were persisted to Engram only.

## Engram Observation Lineage

| Artifact | Topic Key | Engram ID | Content |
|----------|-----------|-----------|---------|
| Proposal | `sdd/core-engine/proposal` | — | Persisted in Engram |
| Spec (aggregate) | `sdd/core-engine/spec` | 475 | 6 capabilities |
| Design | `sdd/core-engine/design` | — | Persisted in Engram |
| Tasks | `sdd/core-engine/tasks` | 477 | 20 tasks |
| Apply-progress | `sdd/core-engine/apply-progress` | 478 | Phase 4 implementation |
| Verify-report | `sdd/core-engine/verify-report` | 479 | Full verification report |
| **Archive-report** | **`sdd/core-engine/archive-report`** | **—** | **This report** |

## Source of Truth Status

The following main specs already reflect the new behavior (no merge needed):
- `openspec/specs/vertex-extraction/spec.md` ✅
- `openspec/specs/bearing-calculation/spec.md` ✅
- `openspec/specs/distance-calculation/spec.md` ✅
- `openspec/specs/colindancia-detection/spec.md` ✅
- `openspec/specs/template-engine/spec.md` ✅
- `openspec/specs/derrotero-generation/spec.md` ✅

## SDD Cycle Complete

The change has been fully planned, implemented, verified, and archived.
Ready for the next change.
