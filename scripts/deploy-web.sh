#!/usr/bin/env bash
# Build and deploy the web app to Cloud Run.
# Supabase values come from apps/web/.env.local; the API URL is always the deployed
# API, never the localhost value used for local development.
set -euo pipefail
cd "$(dirname "$0")/.."

PROJECT=project-1299407e-7d72-48ba-8bb
REGION=asia-south1
API_URL=$(gcloud run services describe gst-recon-api --region "$REGION" --project "$PROJECT" --format='value(status.url)')
IMAGE="$REGION-docker.pkg.dev/$PROJECT/gst-recon/web:latest"

set -a; . apps/web/.env.local; set +a

case "$API_URL" in
  https://*) ;;
  *) echo "refusing to deploy: API URL is '$API_URL'" >&2; exit 1 ;;
esac

gcloud builds submit --project "$PROJECT" --config cloudbuild-web.yaml \
  --substitutions "_SUPABASE_URL=$NEXT_PUBLIC_SUPABASE_URL,_SUPABASE_ANON_KEY=$NEXT_PUBLIC_SUPABASE_ANON_KEY,_API_URL=$API_URL" .
gcloud run deploy gst-recon-web --project "$PROJECT" --image "$IMAGE" --region "$REGION" --quiet
echo "deployed web with API_URL=$API_URL"
