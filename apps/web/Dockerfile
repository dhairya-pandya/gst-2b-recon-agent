# Build from the repo root: docker build -f apps/web/Dockerfile .
# NEXT_PUBLIC_* values are compiled into the bundle, so they are build args.
FROM node:22-slim AS base
RUN corepack enable
WORKDIR /srv/web

FROM base AS deps
COPY apps/web/package.json apps/web/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

FROM base AS build
ARG NEXT_PUBLIC_SUPABASE_URL
ARG NEXT_PUBLIC_SUPABASE_ANON_KEY
ENV NEXT_PUBLIC_SUPABASE_URL=$NEXT_PUBLIC_SUPABASE_URL \
    NEXT_PUBLIC_SUPABASE_ANON_KEY=$NEXT_PUBLIC_SUPABASE_ANON_KEY \
    NEXT_TELEMETRY_DISABLED=1
COPY --from=deps /srv/web/node_modules ./node_modules
COPY apps/web ./
RUN pnpm build

FROM node:22-slim AS run
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 PORT=8080 HOSTNAME=0.0.0.0
WORKDIR /srv/web
COPY --from=build /srv/web/.next/standalone ./
COPY --from=build /srv/web/.next/static ./.next/static
COPY --from=build /srv/web/public ./public
EXPOSE 8080
CMD ["node", "server.js"]
