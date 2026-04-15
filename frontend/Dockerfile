# ─── SwiftClaim Frontend ──────────────────────────────────────────
# Stage 1: Build the React/Vite app
# Stage 2: Serve with Nginx (alpine) — tiny production image
# ──────────────────────────────────────────────────────────────────

# ── BUILD STAGE ──────────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies (cached layer)
COPY package.json package-lock.json ./
RUN npm install

# Copy source and build
COPY . .

# Backend URL can be overridden at build time:
#   docker build --build-arg VITE_API_BASE_URL=https://your-api.com ./frontend
ARG VITE_API_BASE_URL=http://localhost:5001
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

RUN npm run build

# ── SERVE STAGE ──────────────────────────────────────────────────
FROM nginx:stable-alpine

# Copy built assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Custom Nginx config for SPA routing (react-router support)
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
