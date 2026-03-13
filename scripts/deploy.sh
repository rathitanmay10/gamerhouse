#!/usr/bin/env bash
# scripts/deploy.sh
# ─────────────────────────────────────────────────────────────────────────────
# Idempotent bootstrap + deploy script.
# Runs on the EC2 server, called by GitHub Actions over SSH.
# Safe to run multiple times — checks before installing/cloning anything.
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

REPO_URL="https://github.com/tanmayrathi-gkmit/gamerhouse.git"
APP_DIR="/opt/gamerhouse"
BRANCH="${DEPLOY_BRANCH:-dev}"
DOMAIN="${DOMAIN:-gamerhouse.isroot.in}"
IMAGE_NAME="${IMAGE_NAME:-ghcr.io/tanmayrathi-gkmit/gamerhouse:latest}"
NEW_RELIC_LICENSE_KEY="${NEW_RELIC_LICENSE_KEY:-}"
NEW_RELIC_APP_NAME="${NEW_RELIC_APP_NAME:-GamerHouse-Prod}"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  GamerHouse Deploy — $(date '+%Y-%m-%d %H:%M:%S')"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ── 1. Install system dependencies (docker, compose, git, nginx, certbot) ────
install_if_missing() {
  local cmd=$1
  local pkg=${2:-$1}
  if ! command -v "$cmd" &>/dev/null; then
    echo "⏳  Installing $pkg …"
    sudo apt-get update -q
    sudo apt-get install -y -q "$pkg"
    echo "✅  $pkg installed."
  else
    echo "ℹ️   $cmd already installed — skipping."
  fi
}

install_if_missing git git
install_if_missing nginx nginx
install_if_missing certbot certbot

# Python certbot-nginx plugin
if ! dpkg -s python3-certbot-nginx &>/dev/null 2>&1; then
  sudo apt-get install -y -q python3-certbot-nginx
fi

# Docker (engine + compose plugin)
if ! command -v docker &>/dev/null; then
  echo "⏳  Installing Docker …"
  curl -fsSL https://get.docker.com | sudo sh
  sudo usermod -aG docker "$USER"
  echo "✅  Docker installed."
else
  echo "ℹ️   Docker already installed — skipping."
fi

if ! docker compose version &>/dev/null 2>&1; then
  echo "⏳  Installing Docker Compose plugin …"
  sudo apt-get install -y -q docker-compose-plugin
  echo "✅  Docker Compose plugin installed."
else
  echo "ℹ️   Docker Compose plugin already installed — skipping."
fi

# New Relic Infrastructure Agent
if ! command -v newrelic-infra &>/dev/null; then
  echo "⏳  Installing New Relic Infrastructure Agent …"
  # Add New Relic GPG key and repo
  curl -fsSL https://download.newrelic.com/infrastructure_agent/gpg/newrelic-infra.gpg | sudo gpg --dearmor -o /etc/apt/trusted.gpg.d/newrelic-infra.gpg
  echo "deb [arch=amd64] https://download.newrelic.com/infrastructure_agent/linux/apt/ $(lsb_release -sc) main" | sudo tee /etc/apt/sources.list.d/newrelic-infra.list
  
  sudo apt-get update -q
  sudo apt-get install newrelic-infra -y -q
  
  # Configure License Key
  echo "license_key: ${NEW_RELIC_LICENSE_KEY}" | sudo tee /etc/newrelic-infra.yml > /dev/null
  sudo systemctl enable newrelic-infra
  sudo systemctl start newrelic-infra
  echo "✅  New Relic Infrastructure Agent installed."
else
  echo "ℹ️   New Relic Infrastructure Agent already installed — skipping."
fi

# Configure Log Forwarding
LOG_CONF="/etc/newrelic-infra/logging.d/gamerhouse.yml"
if [ ! -f "$LOG_CONF" ]; then
  echo "⏳  Configuring New Relic Log Forwarding …"
  sudo mkdir -p /etc/newrelic-infra/logging.d/
  cat <<EOF | sudo tee "$LOG_CONF" > /dev/null
logs:
  - name: gamerhouse-app
    file: /opt/gamerhouse/logs/application.log
    attributes:
      service: gamerhouse-web
      environment: production
EOF
  sudo systemctl restart newrelic-infra
  echo "✅  Log forwarding configured."
fi

# ── 2. Clone repo or pull latest ─────────────────────────────────────────────
if [ ! -d "$APP_DIR/.git" ]; then
  echo "⏳  Cloning repository …"
  sudo git clone --branch "$BRANCH" "$REPO_URL" "$APP_DIR"
  sudo chown -R "$USER":"$USER" "$APP_DIR"
  echo "✅  Repository cloned."
else
  echo "⏳  Pulling latest code …"
  cd "$APP_DIR"
  git fetch origin
  git reset --hard "origin/$BRANCH"
  echo "✅  Code updated."
fi

cd "$APP_DIR"

# ── 3. Write .env from GitHub Secrets ────────────────────────────────────────
echo "⏳  Writing .env …"
cat > "$APP_DIR/.env" <<EOF
SECRET_KEY=${DJANGO_SECRET_KEY}
DEBUG=False
ALLOWED_HOSTS=${ALLOWED_HOSTS}

POSTGRES_NAME=${POSTGRES_NAME}
POSTGRES_USER=${POSTGRES_USER}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

CELERY_BROKER_URL=${CELERY_BROKER_URL}
CELERY_RESULT_BACKEND=${CELERY_RESULT_BACKEND}
CELERY_TASK_TIME_LIMIT=30
CELERY_TASK_SOFT_TIME_LIMIT=25
CELERY_RESULT_EXPIRES=3600

REDIS_CACHE_URL=${REDIS_CACHE_URL}
AUTH_THROTTLE_RATE=5/minute

EMAIL_HOST=${EMAIL_HOST}
EMAIL_PORT=${EMAIL_PORT}
EMAIL_HOST_USER=${EMAIL_HOST_USER}
EMAIL_HOST_PASSWORD=${EMAIL_HOST_PASSWORD}
DEFAULT_FROM_EMAIL=${DEFAULT_FROM_EMAIL}

FRONTEND_URL=${FRONTEND_URL}

RAZORPAY_KEY_ID=${RAZORPAY_KEY_ID}
RAZORPAY_KEY_SECRET=${RAZORPAY_KEY_SECRET}
RAZORPAY_WEBHOOK_SECRET=${RAZORPAY_WEBHOOK_SECRET}

LOG_LEVEL=INFO
LOG_FILE_ENABLED=True
LOG_CONSOLE_ENABLED=False

NEW_RELIC_LICENSE_KEY=${NEW_RELIC_LICENSE_KEY}
NEW_RELIC_APP_NAME=${NEW_RELIC_APP_NAME}
NEW_RELIC_LOG_LEVEL=info
NEW_RELIC_MONITOR_MODE=true
EOF
chmod 600 "$APP_DIR/.env"   # restrict to owner only — contains secrets
echo "✅  .env written."

# ── 4. Login to GHCR and pull latest image ───────────────────────────────────
echo "⏳  Logging in to GHCR …"
echo "$GHCR_TOKEN" | docker login ghcr.io -u "$GHCR_USER" --password-stdin
echo "✅  GHCR login successful."

echo "⏳  Pulling latest image: $IMAGE_NAME …"
docker pull "$IMAGE_NAME"

# Tag as local gamerhouse_web so docker-compose.yml finds it
docker tag "$IMAGE_NAME" gamerhouse_web:latest
echo "✅  Image pulled and tagged."

# ── 5. Start / restart Docker Compose stack ──────────────────────────────────
echo "⏳  Starting Docker Compose stack …"
docker compose -f "$APP_DIR/docker-compose.yml" up -d --remove-orphans
echo "✅  Stack started."

# ── 6. Health check — wait for app to be ready ───────────────────────────────
echo "⏳  Waiting for /health/ to return 200 …"
MAX=30
COUNT=0
until curl -sf "http://localhost:8000/health/" > /dev/null; do
  COUNT=$((COUNT + 1))
  if [ "$COUNT" -ge "$MAX" ]; then
    echo "❌  App did not become healthy in time. Check: docker compose logs web"
    exit 1
  fi
  echo "   … waiting ($COUNT/$MAX)"
  sleep 5
done
echo "✅  App is healthy."

# ── 7. Configure Nginx (first run only) ──────────────────────────────────────
NGINX_CONF="/etc/nginx/sites-available/gamerhouse"
NGINX_LINK="/etc/nginx/sites-enabled/gamerhouse"

if [ ! -f "$NGINX_CONF" ]; then
  echo "⏳  Installing Nginx config …"
  sudo cp "$APP_DIR/nginx/gamerhouse.conf" "$NGINX_CONF"
  sudo sed -i "s/__DOMAIN__/$DOMAIN/g" "$NGINX_CONF"
  sudo ln -sf "$NGINX_CONF" "$NGINX_LINK"
  sudo nginx -t && sudo systemctl reload nginx
  echo "✅  Nginx configured."
else
  echo "ℹ️   Nginx config already present — skipping."
fi

# ── 8. Obtain SSL cert (first run only) ──────────────────────────────────────
CERT_PATH="/etc/letsencrypt/live/$DOMAIN/fullchain.pem"
if [ ! -f "$CERT_PATH" ]; then
  echo "⏳  Obtaining Let's Encrypt certificate for $DOMAIN …"
  sudo certbot --nginx -d "$DOMAIN" \
    --non-interactive --agree-tos \
    --email "${EMAIL_HOST_USER}" \
    --redirect
  echo "✅  SSL certificate obtained."

  if ! sudo crontab -l 2>/dev/null | grep -qF "certbot renew"; then
    (sudo crontab -l 2>/dev/null; echo "0 3 * * * certbot renew --quiet --post-hook 'systemctl reload nginx'") | sudo crontab -
    echo "✅  Auto-renew cron configured."
  else
    echo "ℹ️   Auto-renew cron already present — skipping."
  fi
else
  echo "ℹ️   SSL certificate already present — skipping certbot."
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✅  Deploy complete!"
echo "  🌐  https://$DOMAIN"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
