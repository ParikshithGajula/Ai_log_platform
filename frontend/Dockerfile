# Stage 1: Build the React app
FROM docker.io/library/node:20-slim AS build
# ↑ Use Node.js 20 image for building. 
#   'AS build' names this stage for later reference.

WORKDIR /app
# ↑ Set working directory to /app.

COPY package*.json ./
# ↑ Copy package.json and package-lock.json first for caching.

RUN npm install
# ↑ Install frontend dependencies.

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

EXPOSE 80
# ↑ Nginx defaults to port 80.

CMD ["nginx", "-g", "daemon off;"]
# ↑ Start Nginx and keep it running in the foreground.
