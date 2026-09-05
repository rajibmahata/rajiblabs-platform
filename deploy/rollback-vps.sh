#!/bin/sh
# RajibLabs — rollback to a previous release (VPS only).
# Usage (on the VPS):  sh /opt/rajiblabs/app/deploy/rollback-vps.sh [<40-hex-sha>]
# Defaults to the newest release dir that is NOT the current .release.
# Safety: RajibLabs paths only (/opt/rajiblabs/releases, /opt/rajiblabs/app);
# PasteControl is never referenced. Data volumes are bind mounts — untouched.
set -eu

APP_DIR=/opt/rajiblabs/app
REL_BASE=/opt/rajiblabs/releases
WANT="${1:-}"

current="$(cat "$APP_DIR/.release" 2>/dev/null || true)"
if [ -z "$WANT" ]; then
  # pick the most recently modified valid candidate that is not current
  newest=""; newest_t=0
  for d in "$REL_BASE"/*/; do
    [ -d "$d" ] || continue
    name=$(basename "$d")
    case "$name" in [0-9a-f]*) [ ${#name} -eq 40 ] || continue;; *) continue;; esac
    [ "$name" = "$current" ] && continue
    t=$(stat -c %Y "$d" 2>/dev/null || stat -f %m "$d" 2>/dev/null || echo 0)
    if [ "$t" -gt "$newest_t" ]; then newest_t="$t"; newest="$name"; fi
  done
  if [ -z "$newest" ]; then
    echo "[ERROR] no previous release found under $REL_BASE"
    exit 1
  fi
  WANT="$newest"
fi
case "$WANT" in
  [0-9a-f]*)
    [ ${#WANT} -eq 40 ] || { echo "[ERROR] not a release SHA: $WANT"; exit 1; };;
  *) echo "[ERROR] not a release SHA: $WANT"; exit 1;;
esac
SRC="$REL_BASE/$WANT"
[ -d "$SRC" ] || { echo "[ERROR] release dir missing: $SRC"; exit 1; }
[ -f "$SRC/docker-compose.production.yml" ] || { echo "[ERROR] compose file missing in $SRC"; exit 1; }
[ -f "$SRC/deploy/deploy-vps.sh" ] || { echo "[ERROR] deploy script missing in $SRC"; exit 1; }

echo "== Rolling back RajibLabs to $WANT (current: ${current:-unknown}) =="
command -v rsync >/dev/null 2>&1 || { echo "[ERROR] rsync not found on VPS (apt install rsync)"; exit 1; }
rsync -a --delete --exclude=.release "$SRC/" "$APP_DIR/"
echo "$WANT" > "$APP_DIR/.release"
DEPLOY_SHA="$WANT" sh "$APP_DIR/deploy/deploy-vps.sh"
