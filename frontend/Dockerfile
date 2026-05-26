# ── Stage 1: build ───────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci

COPY . .
RUN npm run build

# ── Stage 2: production ───────────────────────────────────────────
FROM node:20-alpine AS production

WORKDIR /app
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

COPY --from=builder /app/build ./build
COPY --from=builder /app/package.json ./
RUN npm ci --omit=dev

USER appuser
EXPOSE 3000
ENV NODE_ENV=production PORT=3000

CMD ["node", "build"]

# ── Stage 3: development (hot reload) ────────────────────────────
FROM node:20-alpine AS development

WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci
COPY . .
EXPOSE 3000
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]
