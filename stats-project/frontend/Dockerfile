FROM node:18-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install

# Copy the rest of app
COPY . .

# Expose the default React dev server port
EXPOSE 3000

# Set host to 0.0.0.0 
ENV HOST=0.0.0.0

# Start the development server
CMD ["npm", "start"]