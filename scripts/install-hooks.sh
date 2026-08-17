#!/usr/bin/env bash
# Install the tracked hooks (SECB-WP-FWK-083).
#
# `git clone` does not copy hooks or config, so nothing here is portable by default and a
# downstream that skips this step has no local prevention at all. That is why CI, not this,
# is the authoritative evidence -- see hooks/pre-push.
set -euo pipefail
git config core.hooksPath hooks
echo "core.hooksPath=hooks installed."
echo "NOTE: local hooks are preventive convenience. They are bypassable with --no-verify,"
echo "      are absent in a fresh clone until this runs, and CI remains authoritative."
