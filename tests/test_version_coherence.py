"""The version-coherence gate — `C-AMS-03`.

`SECB-WP-FWK-063`. Review found `AUTO_MERGE_STANDARD.md` declaring `version: 0.2.0`
at commit `86a1f30` while the work package and the pull request called it `0.3.0`.
The parser accepted it, because it checked that the version was well-*formed* and
never that it was the artifact's:

```text
Version field exists ≠ version is syntactically valid
                     ≠ version identifies the artifact being reviewed
```

The gate the operator specified has six conjuncts. **Five are enforced here. One —
`metadata_version_matches_generated_receipt` — is declared `UNSATISFIABLE_NOW`.**
Writing a receipt file by hand and asserting the conjunct holds would reproduce, inside
the gate meant to catch it, the defect `AUTO_MERGE_STANDARD.md` §7 records: a schema is
not a control. It was the easiest conjunct to fake and is therefore the one stated as
absent.

What justifies `UNSATISFIABLE_NOW` is a **text scan over a stated boundary**
(`scripts/*.py`, `.github/**/*.yml`) finding no reference to the schema — *not* a proof
that no producer exists. The first version of this module said the scan checked for a
producer; it checks for a substring, and the two are not the same claim
(`C-AMS-05`).

The manifest is a **separate file** for one reason: a test comparing a document's
version field against itself is circular. `config/artifact_versions.json` is the
independent surface, so a claim needs two places to agree before it counts.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST = REPO_ROOT / "config" / "artifact_versions.json"
STATUS_FILE = REPO_ROOT / "docs" / "09-testing" / "negative_test_status.json"

SEMVER = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


def manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def artifacts() -> list[dict]:
    entries = manifest()["artifacts"]
    assert entries, "an empty manifest would pass every test below vacuously"
    return entries


def declared_metadata(path: Path) -> dict:
    """Read a governed document's own metadata block.

    Duplicated in spirit from `test_auto_merge_standard.py` and deliberately not
    imported: this gate must work for any artifact the manifest lists, not only for
    the one standard, and a cross-import would tie the general gate to a specific
    document's test module.
    """
    lines = path.read_text(encoding="utf-8").splitlines()
    start = next(i for i, line in enumerate(lines[1:], start=1) if line.strip())
    assert lines[start].strip() == "```yaml", f"{path} has no leading metadata fence"
    meta: dict[str, str] = {}
    for line in lines[start + 1:]:
        if line.strip() == "```":
            break
        if line.startswith((" ", "\t")) or ":" not in line:
            continue
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip()
    return meta


# --- conjunct 2: the metadata agrees with an independent surface --------------


def test_declared_version_matches_the_manifest():
    """The defect this gate was opened for, asserted directly."""
    for entry in artifacts():
        meta = declared_metadata(REPO_ROOT / entry["path"])
        assert meta["version"] == entry["version"], (
            f"{entry['path']} declares version {meta['version']!r}; the manifest records "
            f"{entry['version']!r}. One of the two is wrong, and prose in a pull request "
            "is not the tie-breaker"
        )
        assert meta["lifecycle_state"] == entry["lifecycle_state"]
        assert meta["binding"] == str(entry["binding"]).lower()


def test_review_revision_is_a_separate_field_from_version():
    """Fusing the two is the mechanism that produced the defect.

    The original assertion here was `meta["review_revision"] != meta["version"]`,
    which proves nothing: `3` and `0.3.0` differ by token shape whatever the values
    are. Distinctness is now asserted by *type* — a revision is an integer count and
    a version is a semver triple — and forward motion is asserted separately below.
    """
    for entry in artifacts():
        meta = declared_metadata(REPO_ROOT / entry["path"])
        assert "review_revision" in meta, (
            f"{entry['path']} must declare review_revision distinctly from version"
        )
        assert int(meta["review_revision"]) == entry["review_revision"]
        assert not SEMVER.match(meta["review_revision"]), (
            "review_revision is a count, not a version triple"
        )
        assert SEMVER.match(meta["version"]), "version is a semver triple, not a count"


# --- conjunct 5: content cannot change without the record changing -----------


def test_recorded_digest_matches_the_bytes_on_disk():
    """`semantic_change_requires_version_change`, in the enforceable half.

    This detects *any* content change against a stale record, not specifically a
    normative one — it cannot tell a typo from a new section. Recorded in the
    standard's §13 table as `PARTIAL` for exactly that reason: the conjunct's name
    promises more than this instrument delivers.
    """
    for entry in artifacts():
        blob = (REPO_ROOT / entry["path"]).read_bytes()
        assert hashlib.sha256(blob).hexdigest() == entry["sha256"], (
            f"{entry['path']} has changed since the manifest recorded it. Update the "
            "manifest and decide whether the change was normative — if it was, the "
            "version moves too"
        )
        assert len(blob) == entry["bytes"]


# --- conjunct 4: history only moves forward ----------------------------------


def test_version_transitions_are_monotonic():
    for entry in artifacts():
        seen = [h["version"] for h in entry["version_history"] if h["version"]]
        keys = [tuple(int(p) for p in SEMVER.match(v).groups()) for v in seen]
        assert keys == sorted(keys), f"{entry['artifact_id']} history is not monotonic: {seen}"
        current = tuple(int(p) for p in SEMVER.match(entry["version"]).groups())
        assert current >= keys[-1], (
            f"{entry['artifact_id']} current version {entry['version']} is behind its history"
        )


def test_current_review_revision_exceeds_every_historical_revision():
    """`C-AMS-04`.

    ```text
    current_review_revision > max(historical_review_revisions)
    ```

    This assertion was `current == revs[-1]`, which permitted the current entry to
    **repeat** a historical revision while the test's name said *strictly increasing*.
    It did repeat: `86a1f30` and `00e3dae` both declared `review_revision: 3`. The
    name described the intent and the assertion described something weaker — the
    review-revision analogue of a version field that is valid but not the artifact's.
    """
    for entry in artifacts():
        revs = [h["review_revision"] for h in entry["version_history"]]
        assert revs == sorted(set(revs)), f"review_revision repeats or regresses: {revs}"
        assert entry["review_revision"] > max(revs), (
            f"{entry['artifact_id']} current review_revision {entry['review_revision']} does "
            f"not exceed its history {revs}. Equality means two heads claim one revision"
        )


def test_no_revision_number_is_claimed_twice_across_the_whole_ledger():
    """Uniqueness over history *and* current, which the monotonic check alone misses."""
    for entry in artifacts():
        claimed = [h["review_revision"] for h in entry["version_history"]]
        claimed.append(entry["review_revision"])
        assert len(claimed) == len(set(claimed)), (
            f"{entry['artifact_id']} has duplicate review_revision values: {claimed}"
        )


def test_every_recorded_revision_names_the_commit_that_carried_it():
    """A revision without a commit cannot be checked against anything."""
    for entry in artifacts():
        for record in entry["version_history"]:
            assert record.get("commit"), "each historical revision must name its commit"


def test_absent_version_is_null_not_backfilled():
    """A version nobody declared is not history.

    The first revision of the standard had no metadata block. Recording it as
    `0.1.0` would invent a declaration — the same class of error as fabricating a
    taxonomy enumeration for a version that was never measured.
    """
    for entry in artifacts():
        for record in entry["version_history"]:
            if record["version"] is None:
                assert "note" in record and record["note"], (
                    "a null version must carry the reason it is null"
                )


# --- conjunct 6: one version, one digest -------------------------------------


def test_no_two_current_entries_claim_a_version_with_different_digests():
    pairs: dict[tuple[str, str], str] = {}
    for entry in artifacts():
        key = (entry["artifact_id"], entry["version"])
        assert key not in pairs, f"two current entries claim {key}"
        pairs[key] = entry["sha256"]


def test_the_recorded_incoherence_is_marked_superseded_not_silently_dropped():
    """The violation happened in this branch, and the record keeps it.

    `c171e17` and `86a1f30` both declare `0.2.0` with different digests — conjunct 6
    violated in the very history the conjunct exists to protect. The guard exempts
    superseded history and enforces the rule on current entries, so the evidence
    survives without the manifest asserting a false present state.
    """
    for entry in artifacts():
        by_version: dict[str, set[str]] = {}
        for record in entry["version_history"]:
            if record["version"]:
                by_version.setdefault(record["version"], set()).add(record["sha256"])
        for version, digests in by_version.items():
            if len(digests) > 1:
                marked = [
                    h for h in entry["version_history"]
                    if h["version"] == version
                    and h.get("coherence_status") == "SUPERSEDED_INCOHERENT"
                ]
                assert marked, (
                    f"{entry['artifact_id']} history has {len(digests)} digests claiming "
                    f"{version} and none is marked SUPERSEDED_INCOHERENT. An unmarked "
                    "collision is indistinguishable from an unnoticed one"
                )


# --- conjunct 3: declared absent, not faked ----------------------------------


def test_no_receipt_schema_reference_found_within_the_stated_boundary():
    """`AMS-03` / `C-AMS-05` — the observation, at its real strength.

    This test previously carried the name
    `..._nothing_pretends_otherwise` and the claim *"scans for a producer, not for a
    file"*. It does neither. It is a **substring scan over a stated boundary**, and it
    is wrong in both directions: a comment mentioning the schema counts as a producer,
    and a real producer naming its output generically is invisible to it.

    ```text
    Schema token appears in a workflow
      ≠ the workflow produces a receipt
      ≠ the receipt is valid
      ≠ a consumer requires the receipt
    ```

    So what is asserted is `NO_RECEIPT_SCHEMA_REFERENCE_FOUND` over
    `scripts/*.py` and `.github/**/*.yml`, and the scenario must itself declare what
    the scan does not prove. The behavioural contract that would flip the conjunct is
    recorded in `flip_requires` and in the standard's §13 — invoke, validate, verify
    bindings, tamper one, expect rejection.
    """
    scenarios = json.loads(STATUS_FILE.read_text(encoding="utf-8"))["scenarios"]
    ams_03 = next((s for s in scenarios if s["id"] == "AMS-03"), None)
    assert ams_03, "AMS-03 must be declared in negative_test_status.json"
    assert ams_03["status"] == "GAP_REPRODUCED"
    assert ams_03["observation"] == "NO_RECEIPT_SCHEMA_REFERENCE_FOUND"
    assert set(ams_03["boundary"]) == {"scripts/*.py", ".github/**/*.yml"}, (
        "the boundary must be declared, because the scan's value stops at its edge"
    )
    for unproven in (
        "no_producer_exists",
        "no_generic_producer_exists",
        "no_external_producer_exists",
    ):
        assert unproven in ams_03["not_proven"], (
            f"AMS-03 must state that it does not prove {unproven}"
        )

    scanned, hits = 0, []
    for path in sorted((REPO_ROOT / "scripts").glob("*.py")) + sorted(
        (REPO_ROOT / ".github").rglob("*.yml")
    ):
        scanned += 1
        text = path.read_text(encoding="utf-8", errors="replace")
        if "artifact-version-receipt" in text or "artifact_version_receipt" in text:
            hits.append(str(path.relative_to(REPO_ROOT)))
    assert scanned, "an empty boundary would make this assertion vacuous"
    assert not hits, (
        f"{hits} reference the receipt schema. A reference is not a producer — inspect "
        "them, and if a producer now exists, flip AMS-03 on the behavioural contract, "
        "not on this scan"
    )


@pytest.mark.parametrize("conjunct", [
    "metadata_version_is_semver",
    "metadata_version_matches_manifest",
    "metadata_version_matches_generated_receipt",
    "version_transition_is_monotonic",
    "semantic_change_requires_version_change",
    "no_two_active_blobs_claim_same_version_with_different_digest",
])
def test_every_conjunct_has_a_declared_status_in_the_standard(conjunct):
    """No conjunct may be silently unaddressed.

    A six-term conjunction where one term is never mentioned again reads as satisfied.
    Each term must appear in §13's status table, whether its status is `ENFORCED`,
    `PARTIAL` or `UNSATISFIABLE_NOW`.
    """
    text = (REPO_ROOT / "docs" / "00-governance" / "AUTO_MERGE_STANDARD.md").read_text(
        encoding="utf-8"
    )
    short = conjunct if len(conjunct) < 40 else conjunct[:24]
    assert short in text, f"conjunct {conjunct} has no declared status in the standard"
