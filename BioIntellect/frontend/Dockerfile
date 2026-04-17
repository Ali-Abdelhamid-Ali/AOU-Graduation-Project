FROM node:20-alpine AS build_frontend

WORKDIR /app

# Install the dependencies needed to compile the Vite app.
# --legacy-peer-deps is required because @react-three/fiber@8 declares a peer
# on react@^18 using a range that npm 10 treats as a conflict with
# react-router-dom@7. This flag does NOT skip installation — it only suppresses
# the conflict error the same way npm 6 did. No runtime behaviour is affected.
COPY package.json package-lock.json ./
RUN npm ci --legacy-peer-deps

# Copy the source only after dependency installation to keep cache hits stable.
COPY . .

# Vite reads these values at build time and bakes them into the static bundle.
ARG VITE_API_URL=/api
ARG VITE_API_ROOT_URL=/api
ENV VITE_API_URL=${VITE_API_URL}
ENV VITE_API_ROOT_URL=${VITE_API_ROOT_URL}

# Build the production assets in the lightweight builder stage.
RUN npm run build

FROM nginx:1.27-alpine AS runtime

WORKDIR /usr/share/nginx/html

# Keep the nginx routing in a dedicated file so it is easier to maintain.
COPY nginx.conf /etc/nginx/conf.d/default.conf

COPY --from=build_frontend /app/dist/ .

EXPOSE 80

# Keep a simple readiness check so Compose can wait for nginx to be ready.
HEALTHCHECK --interval=20s --timeout=5s --retries=5 CMD wget -qO- http://127.0.0.1/ >/dev/null || exit 1
