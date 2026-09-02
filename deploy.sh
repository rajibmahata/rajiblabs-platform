#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# RajibLabs — one-command FTP deploy
# Uploads the frontend build to SmarterASP via FTP
# Usage: ./deploy.sh [--build]
#   --build   Rebuild frontend before deploying (default: use existing dist/)
#
# Secrets are read from environment variables or a local .env file:
#   FTP_HOST, FTP_USER, FTP_PASS, FTP_PATH, SITE_URL
#   FTP_HOST should be just the hostname, e.g. win1069.site4now.net
#   FTP_PATH should be the verified FTP root, e.g. / or empty if already scoped
# ═══════════════════════════════════════════════════════════════
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR/frontend"
DIST_DIR="$PROJECT_DIR/dist"
ENV_FILE="$SCRIPT_DIR/.env"

# Load local env file if present (do not commit secrets)
if [ -f "$ENV_FILE" ]; then
  # shellcheck disable=SC1090
  set -a
  . "$ENV_FILE"
  set +a
fi

: "${FTP_HOST:=win1069.site4now.net}"
: "${FTP_USER:=rajibmahata143-001}"
: "${FTP_PASS:?Set FTP_PASS in your environment or .env}"
: "${FTP_PATH:=}"
: "${SITE_URL:=https://rajiblabs.com}"

# Normalize FTP_HOST (strip ftp://, :21, trailing slashes) — do not touch password
FTP_HOST_RAW="$FTP_HOST"
FTP_HOST="${FTP_HOST#ftp://}"
FTP_HOST="${FTP_HOST#ftps://}"
FTP_HOST="${FTP_HOST%%/*}"
FTP_HOST="${FTP_HOST%%:*}"
FTP_PATH_RAW="$FTP_PATH"
# FTP_PATH may be "/" for root, or empty, or a subfolder. Keep "/" as empty for root.
if [[ "$FTP_PATH" == "/" ]]; then
  FTP_PATH=""
else
  FTP_PATH="${FTP_PATH#/}"
  FTP_PATH="${FTP_PATH%/}"
fi
# If FTP_PATH still contains host (user set FTP_HOST as ftp://.../rajiblabs), extract
if [[ "$FTP_PATH" == *"win1069"* ]]; then
  FTP_HOST="win1069.site4now.net"
  FTP_PATH=""
fi

DO_BUILD=false
if [[ "${1:-}" == "--build" ]]; then
  DO_BUILD=true
fi

echo ""
echo "🚀 RajibLabs deploy"
echo "───────────────────"
echo "  Host: $FTP_HOST"
echo "  User: $FTP_USER"
if [[ -z "$FTP_PATH" ]]; then
  echo "  Path: / (FTP root)"
else
  echo "  Path: /$FTP_PATH"
fi

if $DO_BUILD; then
  echo "🔨 Building frontend..."
  cd "$PROJECT_DIR"
  npm run build
  echo "✅ Build complete"
fi

if [ ! -f "$DIST_DIR/index.html" ]; then
  echo "❌ dist/index.html not found. Run with --build first."
  exit 1
fi

# ── Auto-detect correct FTP base to avoid /rajiblabs/rajiblabs nesting ──
if command -v lftp >/dev/null 2>&1; then
  echo "🔍 Detecting FTP root (avoid /rajiblabs/rajiblabs)..."
  FTP_ROOT_LIST="/tmp/ftp_root_list_$$"
  lftp -e "set ftp:passive-mode true; set ftp:ssl-allow no; set net:timeout 15; cls -1; bye" -u "$FTP_USER,$FTP_PASS" "$FTP_HOST" > "$FTP_ROOT_LIST" 2>&1 || true
  cat "$FTP_ROOT_LIST" 2>&1 | tr -d '\r' | head -30 > "${FTP_ROOT_LIST}.clean"
  # Debug (no password)
  echo "   FTP root listing (first 20):"
  head -20 "${FTP_ROOT_LIST}.clean" | sed 's/^/     /' || true
  if grep -q "^rajiblabs$" "${FTP_ROOT_LIST}.clean"; then
    echo "   → FTP at account root (contains rajiblabs folder) → site is at /rajiblabs"
    DETECTED="rajiblabs"
  elif grep -q "wwwroot" "${FTP_ROOT_LIST}.clean" || grep -q "^index.html$" "${FTP_ROOT_LIST}.clean" || grep -q "^assets$" "${FTP_ROOT_LIST}.clean"; then
    echo "   → FTP already at site root (/rajiblabs) → using /"
    DETECTED=""
  elif grep -q "^site$" "${FTP_ROOT_LIST}.clean"; then
    echo "   → FTP at site container (contains site/wwwroot) → using site/wwwroot"
    DETECTED="site/wwwroot"
  else
    echo "   → Could not determine, using configured FTP_PATH"
    DETECTED="$FTP_PATH"
  fi
  # Correct misconfigured FTP_PATH that would cause nesting
  if [[ "$FTP_PATH" == "rajiblabs" && "$DETECTED" == "" ]]; then
    echo "   ⚠ Configured FTP_PATH=rajiblabs but FTP is already at /rajiblabs → correcting to / (avoid nested /rajiblabs/rajiblabs)"
    FTP_PATH=""
  elif [[ -z "$FTP_PATH" && "$DETECTED" == "rajiblabs" ]]; then
    echo "   ⚠ FTP is at account root, need /rajiblabs"
    FTP_PATH="rajiblabs"
  elif [[ "$DETECTED" == "site/wwwroot" ]]; then
    FTP_PATH="site/wwwroot"
  elif [[ -n "$DETECTED" && "$DETECTED" != "$FTP_PATH" ]]; then
    echo "   ℹ Using detected path: /$DETECTED (was /$FTP_PATH)"
    FTP_PATH="$DETECTED"
  fi
  rm -f "$FTP_ROOT_LIST" "${FTP_ROOT_LIST}.clean" 2>/dev/null || true
fi

if [[ -z "$FTP_PATH" ]]; then
  echo "📤 Uploading to $FTP_HOST/ (site root)"
else
  echo "📤 Uploading to $FTP_HOST/$FTP_PATH ..."
fi

BUILT_HASH=$(grep -o 'index-[^"]*\.js' "$DIST_DIR/index.html" | head -1 || echo "unknown")
echo "   Built hash: $BUILT_HASH"

# Prefer lftp if available
USE_LFTP=false
if command -v lftp >/dev/null 2>&1; then
  USE_LFTP=true
  echo "  Using lftp (passive, create-dirs)"
else
  echo "  Using curl (install lftp: sudo apt-get install lftp)"
fi

# Helper to upload a single file to the verified FTP root
# Uses -u for auth, never puts password in URL, properly quoted
upload() {
  local src="$1"
  local rel="$2"
  local dest
  if [[ -z "$FTP_PATH" ]]; then
    dest="$rel"
  else
    dest="$FTP_PATH/$rel"
  fi
  # Ensure remote dir exists for this file (lftp mkdir -p, curl --ftp-create-dirs)
  local remote_dir
  remote_dir="$(dirname "$dest")"
  if [[ "$remote_dir" != "." && "$remote_dir" != "/" ]]; then
    if $USE_LFTP; then
      lftp -e "set ftp:passive-mode true; set ftp:ssl-allow no; set net:timeout 30; mkdir -p \"$remote_dir\"; bye" -u "$FTP_USER,$FTP_PASS" "$FTP_HOST" >/dev/null 2>&1 || true
    fi
  fi
  if $USE_LFTP; then
    if lftp -e "set ftp:passive-mode true; set ftp:ssl-allow no; set net:timeout 30; put \"$src\" -o \"$dest\"; bye" -u "$FTP_USER,$FTP_PASS" "$FTP_HOST" >/dev/null 2>&1; then
      echo "  ✓ $rel"
      return 0
    fi
  else
    if curl --fail --ftp-pasv --ftp-create-dirs -u "$FTP_USER:$FTP_PASS" -T "$src" "ftp://$FTP_HOST/$dest" --connect-timeout 30 --max-time 60 >/dev/null 2>&1; then
      echo "  ✓ $rel"
      return 0
    fi
  fi
  echo "  ✗ FAILED: $rel"
  # Verbose retry (still not printing password, -u is safe)
  if $USE_LFTP; then
    lftp -e "set ftp:passive-mode true; set ftp:ssl-allow no; set net:timeout 30; put \"$src\" -o \"$dest\"; bye" -u "$FTP_USER,$FTP_PASS" "$FTP_HOST" 2>&1 | tail -20
  else
    curl --ftp-pasv --ftp-create-dirs -u "$FTP_USER:$FTP_PASS" -T "$src" "ftp://$FTP_HOST/$dest" --connect-timeout 30 -v 2>&1 | tail -30
  fi
  return 1
}

# Upload only to verified FTP_PATH (no brute-force) — prevents overwriting backend web.config and nested
CANDIDATE_PATHS=()
if [[ -z "$FTP_PATH" ]]; then CANDIDATE_PATHS+=(""); else CANDIDATE_PATHS+=("$FTP_PATH"); fi
# Deduplicate
UNIQUE_CANDS=()
for p in "${CANDIDATE_PATHS[@]}"; do
  skip=false
  for q in "${UNIQUE_CANDS[@]}"; do [[ "$p" == "$q" ]] && skip=true && break; done
  $skip || UNIQUE_CANDS+=("$p")
done

upload_multi() {
  local src="$1" rel="$2"
  local ok=false
  for base in "${UNIQUE_CANDS[@]}"; do
    local dest
    if [[ -z "$base" ]]; then dest="$rel"; else dest="$base/$rel"; fi
    # Save original FTP_PATH, temporarily override for upload()
    local saved="$FTP_PATH"
    FTP_PATH="$base"
    if upload "$src" "$rel" 2>&1 | sed "s/^/    [$base] /"; then
      ok=true
    fi
    FTP_PATH="$saved"
  done
  $ok || echo "  ✗ ALL CANDIDATES FAILED: $rel"
}

SW_FILE=""
while IFS= read -r -d '' file; do
  rel="${file#$DIST_DIR/}"
  if [[ "$rel" == "sw.js" ]]; then
    SW_FILE="$file"
    continue
  fi
  echo "→ $rel"
  upload_multi "$file" "$rel" || echo "  ⚠ Continuing after failure for $rel"
done < <(find "$DIST_DIR" -type f -print0)

if [[ -n "$SW_FILE" ]]; then
  echo "  → Uploading sw.js last (all candidates)..."
  if $USE_LFTP; then
    for base in "${UNIQUE_CANDS[@]}"; do
      p="${base:+$base/}sw.js"
      if [[ -z "$base" ]]; then p="sw.js"; fi
      lftp -e "set ftp:passive-mode true; rm -f \"$p\"; bye" -u "$FTP_USER,$FTP_PASS" "$FTP_HOST" 2>&1 | head -5 || true
    done
  fi
  upload_multi "$SW_FILE" "sw.js" || echo "  ⚠ sw.js upload failed — site will still work, PWA may need hard refresh"
fi

# Clean nested deployment only when FTP already at site root (FTP_PATH == ""), never when at account root
if [[ -z "$FTP_PATH" ]] && command -v lftp >/dev/null 2>&1; then
  echo "🧹 Removing nested rajiblabs/rajiblabs if present (previous mis-deploy)..."
  echo "   Listing rajiblabs before delete:"
  lftp -e "set ftp:passive-mode true; set ftp:ssl-allow no; ls rajiblabs; bye" -u "$FTP_USER,$FTP_PASS" "$FTP_HOST" 2>&1 | head -20 || true
  lftp -e "set ftp:passive-mode true; set ftp:ssl-allow no; rm -r rajiblabs/index.html; rm -r rajiblabs/assets; rm rajiblabs/index.html; rmdir rajiblabs; bye" -u "$FTP_USER,$FTP_PASS" "$FTP_HOST" 2>&1 | head -20 || true
  lftp -e "set ftp:passive-mode true; set ftp:ssl-allow no; rm -r rajiblabs; bye" -u "$FTP_USER,$FTP_PASS" "$FTP_HOST" 2>&1 | head -20 || true
  echo "   Verify after delete:"
  lftp -e "set ftp:passive-mode true; ls rajiblabs; bye" -u "$FTP_USER,$FTP_PASS" "$FTP_HOST" 2>&1 | head -20 || echo "   rajiblabs nested cleaned (not found)"
else
  echo "   Skip nested cleanup (FTP at account root, rajiblabs is docroot)"
fi

echo ""
echo "🔍 Verifying deployment (built $BUILT_HASH vs live)..."
if title=$(curl -s --max-time 30 "$SITE_URL" | grep -o '<title>[^<]*</title>' | sed 's/<[^>]*>//g' | head -1); then
  echo "   Title: ${title:-<empty>}"
fi
LIVE_HASH=$(curl -s --max-time 15 "$SITE_URL" | grep -o 'index-[^"]*\.js' | head -1 || echo "none")
echo "   Live hash: $LIVE_HASH"
if [[ "$LIVE_HASH" == "$BUILT_HASH" ]]; then
  echo "   ✅ Live matches built — deploy verified"
else
  echo "   ⚠ Live ($LIVE_HASH) != built ($BUILT_HASH) — may need cache purge or FTP path is not docroot. Check candidates above."
  echo "   Trying to list which candidate path would serve index.html..."
  for base in "${UNIQUE_CANDS[@]}"; do
    url="$SITE_URL/${base:+$base/}index.html"
    code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$url" || echo "000")
    echo "     $url -> $code"
  done
fi
if curl -s --head --max-time 10 "$SITE_URL/manifest.webmanifest" | grep -q "200"; then
  echo "   PWA manifest: OK"
else
  echo "   PWA manifest: not yet (may need a minute to propagate)"
fi

echo ""
echo "✅ Deployment complete"
echo "   $SITE_URL"
echo "   https://rajiblabs.com"
