# Use Node.js to build the app
FROM node:18-alpine AS build

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci

# Copy the rest of your app
COPY . .

# Build the React app (will use .env if present in /app or /app/src)
RUN npm run build

# Use a lightweight image to serve the build
FROM node:18-alpine

WORKDIR /app

# Install serve globally
RUN npm install -g serve

# Copy the build output from the previous stage
COPY --from=build /app/build ./build

# Expose the port you want to use (e.g., 9000)
EXPOSE 9000

# Serve the app on port 9000
CMD ["serve", "-s", "build", "-l", "9000"]