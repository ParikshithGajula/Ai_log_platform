# Stage 1: Build the React app
FROM docker.io/library/node:20-slim AS build
# ↑ Use Node.js 20 image for building. 
#   'AS build' names this stage for later reference.

WORKDIR /app
# ↑ Set working directory to /app.

COPY package*.json ./
# ↑ Copy package.json and package-lock.json first for caching.

# VITE_API_URL is baked at build time — pass via --build-arg
ARG VITE_API_URL=http://localhost:8000
ARG VITE_BASE_PATH=/Ai_log_platform/
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_BASE_PATH=$VITE_BASE_PATH

RUN npm ci
# ↑ Clean install for reproducible builds.

COPY . .
# ↑ Copy all frontend code.

RUN npm run build
# ↑ Build the production-ready React app.

# Stage 2: Serve the app with Nginx
FROM docker.io/library/nginx:alpine
# ↑ Use Nginx image to serve static files. 
#   'alpine' is a tiny Linux distribution, making the final image very small.

COPY --from=build /app/dist /usr/share/nginx/html
# ↑ Copy ONLY the built files from Stage 1 into Nginx's public folder.
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
# ↑ Nginx defaults to port 80.

CMD ["nginx", "-g", "daemon off;"]
# ↑ Start Nginx and keep it running in the foreground.
