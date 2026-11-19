#!/usr/bin/env bash
# Build and deploy Milaan's web app to Cloud Run as the single public URL.
# The browser only talks to this service; /api/* is proxied server-side to the API,
# whose address is a runtime env var (API_ORIGIN), not baked into the bundle.
set -euo pipefail
cd "$(dirname "$0")/.."

PROJECT=project-1299407e-7d72-48ba-8bb
REGION=asia-south1
SERVICE=milaan
API_URL=$(gcloud run services describe gst-recon-api --region "$REGION" --project "$PROJECT" --format='value(status.url)')
IMAGE="$REGION-docker.pkg.dev/$PROJECT/gst-recon/milaan-web:latest"

set -a; . apps/web/.env.local; set +a

case "$API_URL" in
  https://*) ;;
  *) echo "refusing to deploy: API URL is '$API_URL'" >&2; exit 1 ;;
esac

gcloud builds submit --project "$PROJECT" --config cloudbuild-web.yaml \
  --substitutions "_SUPABASE_URL=$NEXT_PUBLIC_SUPABASE_URL,_SUPABASE_ANON_KEY=$NEXT_PUBLIC_SUPABASE_ANON_KEY" .
gcloud run deploy "$SERVICE" --project "$PROJECT" --image "$IMAGE" --region "$REGION" \
  --allow-unauthenticated --set-env-vars "API_ORIGIN=$API_URL" --quiet
echo "deployed $SERVICE (API_ORIGIN=$API_URL)"
