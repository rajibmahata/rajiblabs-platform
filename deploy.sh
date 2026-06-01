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

echo "📤 Uploading to $FTP_HOST..."

upload() {
  local src="$1"
  local dest="$2"
  if curl -s --fail -u "$FTP_USER:$FTP_PASS" -T "$src" "ftp://$FTP_HOST/$FTP_PATH/$dest" >/dev/null 2>&1; then
    echo "  ✓ $dest"
  else
    echo "  ✗ FAILED: $dest"
    return 1
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
