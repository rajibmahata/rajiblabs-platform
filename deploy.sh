#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# RajibLabs — one-command FTP deploy
# Uploads the frontend build to SmarterASP via FTP
# Usage: ./deploy.sh [--build]
#   --build   Rebuild frontend before deploying (default: use existing dist/)
#
# Secrets are read from environment variables or a local .env file:
#   FTP_HOST, FTP_USER, FTP_PASS, FTP_PATH, SITE_URL
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
: "${FTP_PATH:=rajiblabs}"
: "${SITE_URL:=http://rajibmahata143-001-site1.mtempurl.com/}"

DO_BUILD=false
if [[ "${1:-}" == "--build" ]]; then
  DO_BUILD=true
fi

echo ""
echo "🚀 RajibLabs deploy"
echo "───────────────────"

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

echo "📤 Uploading to $FTP_HOST/$FTP_PATH ... (also trying site/wwwroot for custom domain)"

# Prefer lftp (more reliable for SmarterASP) if available, else curl
USE_LFTP=false
if command -v lftp >/dev/null 2>&1; then
  USE_LFTP=true
  echo "  Using lftp for upload (passive, create-dirs)"
else
  echo "  Using curl for upload (install lftp for more reliability: sudo apt-get install lftp)"
fi

upload() {
  local src="$1"
  local dest="$2"
  local target1="$FTP_PATH/$dest"
  local target2="site/wwwroot/$dest"
  # Try primary path first, then fallback to site/wwwroot (custom domain root on SmarterASP)
  for target in "$target1" "$target2"; do
    if $USE_LFTP; then
      if lftp -e "set ftp:passive-mode true; set ftp:ssl-allow no; put \"$src\" -o \"$target\"; bye" -u "$FTP_USER,$FTP_PASS" "$FTP_HOST" >/dev/null 2>&1; then
        # Only log once for primary
        if [[ "$target" == "$target1" ]]; then
          echo "  ✓ $dest"
        fi
        return 0
      fi
    else
      if curl --fail --ftp-pasv --ftp-create-dirs -u "$FTP_USER:$FTP_PASS" -T "$src" "ftp://$FTP_HOST/$target" --connect-timeout 30 --max-time 60 >/dev/null 2>&1; then
        if [[ "$target" == "$target1" ]]; then
          echo "  ✓ $dest"
        fi
        return 0
      fi
    fi
  done
  # If both failed, show verbose for primary
  echo "  ✗ FAILED: $dest — retry verbose for $target1 ..."
  if $USE_LFTP; then
    lftp -e "set ftp:passive-mode true; set ftp:ssl-allow no; put \"$src\" -o \"$target1\"; bye" -u "$FTP_USER,$FTP_PASS" "$FTP_HOST" 2>&1 | tail -20
  else
    curl --ftp-pasv --ftp-create-dirs -u "$FTP_USER:$FTP_PASS" -T "$src" "ftp://$FTP_HOST/$target1" --connect-timeout 30 -v 2>&1 | tail -30
  fi
  return 1
}

# Upload every file in dist, preserving directory structure.
# Upload sw.js last (service worker can be locked if served)
SW_FILE=""
while IFS= read -r -d '' file; do
  rel="${file#$DIST_DIR/}"
  if [[ "$rel" == "sw.js" ]]; then
    SW_FILE="$file"
    continue
  fi
  upload "$file" "$rel" || echo "  ⚠ Continuing after failure for $rel"
done < <(find "$DIST_DIR" -type f -print0)

# Upload sw.js last with extra handling
if [[ -n "$SW_FILE" ]]; then
  echo "  → Uploading sw.js last (service worker)..."
  # Try to remove old sw.js first (if locked, this may fail but ok)
  if $USE_LFTP; then
    lftp -e "set ftp:passive-mode true; rm -f \"$FTP_PATH/sw.js\"; bye" -u "$FTP_USER,$FTP_PASS" "$FTP_HOST" 2>&1 | head -5 || true
  fi
  upload "$SW_FILE" "sw.js" || echo "  ⚠ sw.js upload failed — site will still work, but PWA may need hard refresh"
fi

echo ""
echo "🔍 Verifying deployment..."
if title=$(curl -s --max-time 30 "$SITE_URL" | grep -o '<title>[^<]*</title>' | sed 's/<[^>]*>//g' | head -1); then
  echo "   Title: ${title:-<empty>}"
fi

echo ""
echo "✅ Deployment complete"
echo "   $SITE_URL"
echo "   http://rajiblabs.com"
