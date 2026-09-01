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

echo "📤 Uploading to $FTP_HOST${FTP_PATH:+/$FTP_PATH} ..."

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

# Upload all files, sw.js last (service worker can be locked)
SW_FILE=""
while IFS= read -r -d '' file; do
  rel="${file#$DIST_DIR/}"
  if [[ "$rel" == "sw.js" ]]; then
    SW_FILE="$file"
    continue
  fi
  upload "$file" "$rel" || echo "  ⚠ Continuing after failure for $rel"
done < <(find "$DIST_DIR" -type f -print0)

if [[ -n "$SW_FILE" ]]; then
  echo "  → Uploading sw.js last..."
  if $USE_LFTP; then
    lftp -e "set ftp:passive-mode true; rm -f \"$FTP_PATH/sw.js\"; bye" -u "$FTP_USER,$FTP_PASS" "$FTP_HOST" 2>&1 | head -5 || true
    lftp -e "set ftp:passive-mode true; rm -f \"sw.js\"; bye" -u "$FTP_USER,$FTP_PASS" "$FTP_HOST" 2>&1 | head -5 || true
  fi
  upload "$SW_FILE" "sw.js" || echo "  ⚠ sw.js upload failed — site will still work, PWA may need hard refresh"
fi

echo ""
echo "🔍 Verifying deployment..."
if title=$(curl -s --max-time 30 "$SITE_URL" | grep -o '<title>[^<]*</title>' | sed 's/<[^>]*>//g' | head -1); then
  echo "   Title: ${title:-<empty>}"
fi
# Also verify that the new assets are reachable (not old GH7bam2)
if curl -s --head --max-time 10 "$SITE_URL/manifest.webmanifest" | grep -q "200"; then
  echo "   PWA manifest: OK"
else
  echo "   PWA manifest: not yet (may need a minute to propagate)"
fi

echo ""
echo "✅ Deployment complete"
echo "   $SITE_URL"
echo "   https://rajiblabs.com"
