# ============================================
# Frontend — Multi-stage build
# ============================================
FROM node:20-alpine AS base
WORKDIR /app

# Install deps
COPY package.json package-lock.json* ./
RUN npm ci

# ============================================
FROM base AS builder
COPY . .
RUN npm run build

# ============================================
FROM node:20-alpine AS production
WORKDIR /app

ENV NODE_ENV=production
ENV PORT=4000
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

EXPOSE 4000
CMD ["node", "server.js"]

# ============================================
FROM base AS development
COPY . .
EXPOSE 4000
CMD ["npm", "run", "dev"]
