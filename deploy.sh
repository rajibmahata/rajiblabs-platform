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

echo "📤 Uploading to $FTP_HOST/$FTP_PATH ..."

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
  if $USE_LFTP; then
    # lftp handles dirs and passive automatically, single connection
    if lftp -e "set ftp:passive-mode true; set ftp:ssl-allow no; put \"$src\" -o \"$FTP_PATH/$dest\"; bye" -u "$FTP_USER,$FTP_PASS" "$FTP_HOST" 2>&1 | grep -v "^$" | head -20; then
      echo "  ✓ $dest"
      return 0
    else
      echo "  ✗ FAILED (lftp): $dest"
      return 1
    fi
  else
    if curl --fail --ftp-pasv --ftp-create-dirs -u "$FTP_USER:$FTP_PASS" -T "$src" "ftp://$FTP_HOST/$FTP_PATH/$dest" --connect-timeout 30 --max-time 60 2>&1 | grep -v "^$" | head -20; then
      echo "  ✓ $dest"
    else
      local code=$?
      echo "  ✗ FAILED (curl $code): $dest — retry verbose..."
      curl --ftp-pasv --ftp-create-dirs -u "$FTP_USER:$FTP_PASS" -T "$src" "ftp://$FTP_HOST/$FTP_PATH/$dest" --connect-timeout 30 -v 2>&1 | tail -30
      return 1
    fi
  fi
}

# Upload every file in dist, preserving directory structure.
while IFS= read -r -d '' file; do
  rel="${file#$DIST_DIR/}"
  upload "$file" "$rel"
done < <(find "$DIST_DIR" -type f -print0)

echo ""
echo "🔍 Verifying deployment..."
if title=$(curl -s --max-time 30 "$SITE_URL" | grep -o '<title>[^<]*</title>' | sed 's/<[^>]*>//g' | head -1); then
  echo "   Title: ${title:-<empty>}"
fi

echo ""
echo "✅ Deployment complete"
echo "   $SITE_URL"
echo "   http://rajiblabs.com"
