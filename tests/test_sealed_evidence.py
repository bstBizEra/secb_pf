"""Gate 7 (Evidence), mechanized: the sealed MVP package must be bit-stable.

`NFR-04` states that sealed evidence is bit-stable and names its verification
method as *"digest recomputation in review records"* — by hand. Nothing
recomputed it: before `SECB-WP-FWK-045`, `grep -rln "sha256\\|hashlib"` over
`tests/`, `scripts/` and `.github/` returned nothing, while five digests sat
recorded in `SECB-WP-ENGLOOP-MVP-001_INDEPENDENT_REVIEW.md`.

The risk is demonstrated rather than theoretical, and by the author of this
file: **`pytest` wrote cache artifacts into the sealed directory twice in one
session.** The `FWK-009` certification voids on any change to that package, so
a silent mutation destroys a certification with nothing to notice.

The digests below are deliberately a **second copy** of the review record's.
That duplication is the mechanism: this copy is the tripwire, the record's copy
is the evidence. A test that read the digests *from* the record would pass
happily if someone edited both.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SEALED = (
    REPO_ROOT
    / "docs/06-agent-orchestration/skill-router"
    / "SECB-WP-ENGLOOP-MVP-001 — Sandbox Evidence"
)

# Recorded in docs/13-evidence/SECB-WP-ENGLOOP-MVP-001_INDEPENDENT_REVIEW.md
# under review REV-SECB-ENGLOOP-MVP-001-20260810. A mismatch here is a finding,
# never a reason to update these values.
RECORDED = {
    "router.py": "4d1dab78b30eff24b5b4a6202ef84d23c814fb9efed63da049d501eb53eecef2",
    "test_router.py": "8db87b0fe89fa3954f6fb1759d427f9b27da45fa993372b48fb51ecf996ec1d0",
    "SECB-WP-ENGLOOP-MVP-001.md": "261f506bc1a708aff0c90e4250eb49f3b56c6b7fa4cee7469ee5b2b720ab9f04",
    "README.md": "96001a35c1afdbf463299cb31f2bc93277e5a1ce49fa5ca9d42d4c9737681549",
    "EVIDENCE_RECORD.md": "505bd433b5b2b95845f559a13794552a98cc16af57ccd653a34f37c00f7d2d12",
}

# The sixth file carries no recorded digest: the review request was written
# before the package was sealed, so it is part of the directory but not of the
# certified set. Named explicitly, because an unlisted file and an unnoticed
# file must not look alike.
UNSEALED_BUT_EXPECTED = {"INDEPENDENT_REVIEW_REQUEST.md"}


def digest(path: Path) -> str:
    """SHA-256 of *path*, read in binary and never written to."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_every_recorded_digest_still_matches():
    """The whole gate. Five files, five digests, no tolerance."""
    mismatches = []
    for name, expected in sorted(RECORDED.items()):
        path = SEALED / name
        assert path.is_file(), f"sealed file missing: {name}"
        actual = digest(path)
        if actual != expected:
            mismatches.append(f"{name}: recorded {expected[:16]}… actual {actual[:16]}…")
    assert not mismatches, (
        "sealed evidence has changed, which voids the FWK-009 certification:\n  "
        + "\n  ".join(mismatches)
        + "\nThe recorded digests are the baseline. Do not update them to match — "
        "find out what wrote to the sealed package."
    )


def test_the_sealed_directory_contains_nothing_unexpected():
    """A stray artifact is how this package was polluted, twice.

    `pytest` cache directories are the specific offender. The suite runs with
    `-p no:cacheprovider` and `PYTHONDONTWRITEBYTECODE=1`, and this assertion
    is what notices if either is ever dropped.
    """
    present = {p.name for p in SEALED.iterdir()}
    expected = set(RECORDED) | UNSEALED_BUT_EXPECTED
    unexpected = sorted(present - expected)
    assert not unexpected, (
        f"unexpected entries in the sealed package: {unexpected}. "
        "Something wrote into a byte-frozen directory — most likely a pytest "
        "cache or a __pycache__, which is why the suite runs with "
        "-p no:cacheprovider and PYTHONDONTWRITEBYTECODE=1."
    )
    missing = sorted(expected - present)
    assert not missing, f"sealed package is incomplete: {missing}"


def test_a_mutation_would_be_caught(tmp_path):
    """The guard proven to fail, without touching the sealed package (`KN-001`).

    Mutating the real file to demonstrate the failure would risk leaving the
    package dirty if the test aborted between mutation and restore. So the
    proof is done on a copy: the same comparison, applied to altered bytes,
    must produce a mismatch.
    """
    original = (SEALED / "router.py").read_bytes()
    copy = tmp_path / "router.py"
    copy.write_bytes(original + b"\n# one appended comment\n")
    assert digest(copy) != RECORDED["router.py"], (
        "appending a single comment must change the digest, or the comparison "
        "is not detecting anything"
    )
    # and the untouched original still matches, so the fixture proves the
    # detector rather than a broken read
    assert hashlib.sha256(original).hexdigest() == RECORDED["router.py"]


def test_the_recorded_digests_agree_with_the_review_record():
    """The two copies must not drift.

    The duplication is deliberate — this file is the tripwire and the review
    record is the evidence — but a tripwire set to the wrong value is worse
    than none, so the values are compared. `SECB-WP-FWK-044` learned this the
    expensive way: a machine-readable record and its prose drifted, every test
    passed, and a published figure was wrong for two work packages.
    """
    record = (
        REPO_ROOT
        / "docs/13-evidence/SECB-WP-ENGLOOP-MVP-001_INDEPENDENT_REVIEW.md"
    ).read_text(encoding="utf-8")
    for name, expected in sorted(RECORDED.items()):
        assert expected in record, (
            f"{name}'s digest in this test does not appear in the review record — "
            "the tripwire and the evidence have drifted"
        )
