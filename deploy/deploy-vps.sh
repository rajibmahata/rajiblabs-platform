#!/bin/sh
# RajibLabs — VPS deploy (169.58.165.10, shared box with PasteControl).
# Run on the VPS from /opt/rajiblabs/app:
#   sh deploy/deploy-vps.sh
# Safety rules:
#   - never runs `down -v`, never touches /opt/rajiblabs/data
#   - refuses to deploy with empty required secrets
#   - health-gates the API before declaring success
#   - never touches PasteControl: disjoint host ports (:8080 vs :80/:443),
#     own containers/networks/volumes/paths. No shared Docker resources.
set -eu

APP_DIR="/opt/rajiblabs/app"
ENV_FILE="/opt/rajiblabs/config/.env"
COMPOSE="docker-compose.production.yml"
# Shared box: the live app owns :80/:443 — our edge is :8080 (Phase 1).
SITE="http://127.0.0.1:8080"
PUBLIC="http://169.58.165.10:8080"

cd "$APP_DIR"
echo "== RajibLabs VPS deploy =="

# ── 1. Preflight: tooling ──
command -v docker >/dev/null 2>&1 || { echo "[ERROR] docker not found"; exit 1; }
docker compose version >/dev/null 2>&1 || { echo "[ERROR] 'docker compose' plugin not found"; exit 1; }
docker info >/dev/null 2>&1 || { echo "[ERROR] docker daemon not running"; exit 1; }
[ -f "$COMPOSE" ] || { echo "[ERROR] $COMPOSE not found in $APP_DIR"; exit 1; }
[ -f "$ENV_FILE" ] || {
  echo "[ERROR] $ENV_FILE missing."
  echo "  cp deploy/dotenv.production.example $ENV_FILE  # then fill secrets"
  exit 1
}
command -v curl >/dev/null 2>&1 || { echo "[ERROR] curl not found (needed for smoke tests)."; exit 1; }

# ── 1b. Shared-box preflight: :80/:443 must NOT belong to us ──
# (PasteControl owns the public edge; we only ever bind :8080 + localhost.
# If this ever reports our containers on :80/:443, STOP — config drift.)
if command -v ss >/dev/null 2>&1; then
  taken80=$(ss -ltn 2>/dev/null | grep -cE ":(80|443) " || true)
  if [ "$taken80" = "0" ]; then
    echo "[WARN] nothing is listening on :80/:443 — the VPS edge proxy may be down."
    echo "       RajibLabs on :8080 still works directly; Phase-2 domain routing needs the edge up."
  fi
fi

# ── 2. Preflight: required secrets (fail safe — app would 500 in prod) ──
# shellcheck disable=SC1090
set -a; . "$ENV_FILE"; set +a
missing=""
for var in ADMIN_INITIAL_PASSWORD SECRET_KEY JWT_SECRET; do
  val="$(eval "echo \"\${$var:-}\"")"
  if [ -z "$val" ] || [ ${#val} -lt 16 ]; then
    missing="$missing $var"
  fi
done
if [ -n "$missing" ]; then
  echo "[ERROR] refusing deploy — set these in $ENV_FILE (min 16 chars):$missing"
  exit 1
fi

# ── 3. Host dirs + gateway config (create, never overwrite live config) ──
mkdir -p /opt/rajiblabs/config/nginx /opt/rajiblabs/data/mongo \
         /opt/rajiblabs/data/qdrant /opt/rajiblabs/data/uploads /opt/rajiblabs/logs/nginx
if [ ! -f /opt/rajiblabs/config/nginx/gateway.conf ]; then
  cp deploy/nginx/gateway.conf /opt/rajiblabs/config/nginx/gateway.conf
  echo "  - installed gateway.conf (edit live copy at /opt/rajiblabs/config/nginx/)"
fi

# ── 3b. Shared-box preflight: :8080 must be free or already ours ──
if command -v ss >/dev/null 2>&1; then
  if ss -ltn 2>/dev/null | grep -q ":8080 " && \
     [ "$(docker ps --format '{{.Names}}' 2>/dev/null | grep -c '^rajiblabs-gateway$')" = "0" ]; then
    echo "[ERROR] host :8080 is taken by something other than rajiblabs-gateway."
    ss -ltnp 2>/dev/null | grep ":8080 " || true
    exit 1
  fi
fi

# ── 4. Build + start (data volumes are bind mounts — always preserved) ──
# Rollback reference: revision being deployed + current image IDs (the prior
# build is restored via sh deploy/rollback-vps.sh [<sha>] — no git needed).
echo "Deploying revision: ${DEPLOY_SHA:-unknown} (see $APP_DIR/.release after success)"
docker images --format '{{.Repository}}:{{.Tag}} {{.ID}}' rajiblabs-ai-api rajiblabs-frontend 2>/dev/null || true
docker compose -p rajiblabs -f "$COMPOSE" --env-file "$ENV_FILE" up -d --build

# ── 5. Health-gate the API (max ~3 min), then smoke-test the edge ──
echo "Waiting for ai-api to turn healthy..."
tries=0
until [ "$(docker inspect -f '{{.State.Health.Status}}' rajiblabs-ai-api 2>/dev/null)" = "healthy" ]; do
  tries=$((tries + 1))
  if [ "$tries" -gt 36 ]; then
    echo "[ERROR] ai-api never turned healthy:"
    docker compose -p rajiblabs -f "$COMPOSE" --env-file "$ENV_FILE" logs --tail=50 ai-api
    exit 1
  fi
  sleep 5
done
echo "  - ai-api healthy"

fail=0
check() {  # check <label> <url>
  if curl -fsS --max-time 10 "$2" >/dev/null 2>&1; then
    echo "  - $1 OK ($2)"
  else
    echo "  - $1 FAILED ($2)"
    fail=1
  fi
}
check "gateway /health"      "$SITE/health"
check "gateway /api/health"  "$SITE/api/health"
check "gateway /"            "$SITE/"
check "projects API"         "$SITE/api/projects"
if [ "$fail" -ne 0 ]; then
  echo "[ERROR] smoke tests failed — inspect with:"
  echo "  docker compose -p rajiblabs -f $COMPOSE --env-file $ENV_FILE logs --tail=100"
  exit 1
fi

echo ""
echo "Deploy OK: $PUBLIC  (API: /api/*, health: /health)"
echo "Admin:     $PUBLIC/admin/login  (first run seeds admin from ADMIN_INITIAL_PASSWORD)"
echo "Phase 2 (rajiblabs.com, after DNS points here): certbot cert, add the blocks from"
echo "  deploy/nginx/rajiblabs-behind-proxy.conf to the existing edge proxy,"
echo "  verify with 'nginx -t', then reload — https://rajiblabs.com is live."
echo "Migrate legacy SQLite data (one-off, optional — run ON the VPS host):"
echo "  git show <sha>:backend/RajibLabs.Api/rajiblabs.db > /tmp/rajiblabs.db"
echo "  cd /opt/rajiblabs/app/rajiblabs-ai-backend && pip install -r requirements.txt"
echo "  DATABASE_URL=mongodb://127.0.0.1:27017/rajiblabs python scripts/migrate_sqlite_to_mongo.py /tmp/rajiblabs.db"
