FROM node:22-alpine AS base
WORKDIR /app
RUN apk add --no-cache libc6-compat

# Install dependencies only when needed
FROM base AS deps
WORKDIR /app
COPY package*.json ./
# Using npm install to allow package.json changes without strict lock file sync
RUN --mount=type=cache,target=/root/.npm \
    npm install --legacy-peer-deps

# Development image, copy all the files and run next
FROM base AS dev
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
# Environment variables will be injected by docker-compose
EXPOSE 3000
CMD ["npm", "run", "dev"]

# Rebuild the source code only when needed
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Build args
ARG NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
ARG NEXT_PUBLIC_API_URL
ARG NEXT_PUBLIC_APP_URL
ARG INTERNAL_API_URL
ENV NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=$NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_APP_URL=$NEXT_PUBLIC_APP_URL
ENV INTERNAL_API_URL=$INTERNAL_API_URL
ENV NODE_ENV=production

RUN npm run build

# Verify middleware was compiled into standalone output
RUN test -f .next/standalone/.next/server/middleware.js \
    && echo "✅ middleware.js found in standalone output" \
    || (echo "❌ middleware.js NOT found — listing .next/server/:" && ls -la .next/server/ && ls -la .next/standalone/.next/server/ 2>/dev/null; exit 1)

# Production image, copy all the files and run next
FROM base AS runner
WORKDIR /app
ENV NODE_ENV=production

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public

# Set the correct permission for prerender cache
RUN mkdir .next
RUN chown nextjs:nodejs .next

# Automatically leverage output traces to reduce image size
# https://nextjs.org/docs/advanced-features/output-file-tracing
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["node", "server.js"]
