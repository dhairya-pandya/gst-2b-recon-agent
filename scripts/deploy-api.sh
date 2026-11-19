#!/usr/bin/env bash
# Build the API image and roll it out. Existing env vars and secrets on the service are kept.
set -euo pipefail
cd "$(dirname "$0")/.."
PROJECT=project-1299407e-7d72-48ba-8bb
REGION=asia-south1
IMAGE="$REGION-docker.pkg.dev/$PROJECT/gst-recon/api:latest"
# Project URL for the JWKS (ES256 session tokens). Public value, read from the local env file.
SUPABASE_URL=$(grep -E "^SUPABASE_URL=" services/api/.env | cut -d= -f2-)
gcloud builds submit --project "$PROJECT" --config cloudbuild.yaml .
gcloud run deploy gst-recon-api --project "$PROJECT" --image "$IMAGE" --region "$REGION" \
  --update-env-vars "SUPABASE_URL=$SUPABASE_URL" --quiet
