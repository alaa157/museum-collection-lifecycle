FROM node:22-alpine AS dependencies

WORKDIR /app

RUN corepack enable && corepack prepare pnpm@10.12.1 --activate

COPY package.json pnpm-lock.yaml ./

RUN pnpm install --frozen-lockfile

FROM node:22-alpine AS builder

ENV NODE_ENV=production

WORKDIR /app

RUN corepack enable && corepack prepare pnpm@10.12.1 --activate

COPY --from=dependencies /app/node_modules ./node_modules
COPY package.json pnpm-lock.yaml ./
COPY . .

ARG API_GATEWAY_URL=http://127.0.0.1:8000
ENV API_GATEWAY_URL=${API_GATEWAY_URL}

RUN pnpm build

FROM node:22-alpine AS runtime

ENV NODE_ENV=production

WORKDIR /app

RUN addgroup --system --gid 10001 app \
    && adduser --system --uid 10001 --ingroup app app

COPY --from=builder --chown=app:app /app/.next/standalone ./
COPY --from=builder --chown=app:app /app/.next/static ./.next/static

USER app

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD ["node", "-e", "fetch('http://127.0.0.1:3000/').then(r => { if (!r.ok) process.exit(1) }).catch(() => process.exit(1))"]

CMD ["node", "server.js"]
