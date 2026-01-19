FROM node:22-alpine

WORKDIR /app

# Install dependencies only when needed
COPY package*.json ./
RUN npm install --legacy-peer-deps

# Copy source code
COPY . .

# Pass build-time environment variables
ARG NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
ENV NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=$NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY

EXPOSE 3000

# Start in development mode with hot reload
CMD ["npm", "run", "dev"]
