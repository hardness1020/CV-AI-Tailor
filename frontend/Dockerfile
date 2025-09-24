# Frontend Dockerfile for CV Tailor React App
FROM node:20-slim

# Set working directory
WORKDIR /app

# Install dependencies first (for better caching)
COPY package*.json ./
RUN npm ci

# Copy source code (excluding test files via .dockerignore)
COPY . .

# Fix any permission issues
USER root
RUN chown -R node:node /app
USER node

# Expose port 3000
EXPOSE 3000

# Start development server
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]