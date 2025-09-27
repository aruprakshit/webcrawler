FROM node:24-alpine

# Create non-root user with UID/GID 1000
RUN addgroup -g 1000 appuser && \
  adduser -D -u 1000 -G appuser appuser

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production && npm cache clean --force

# Copy application code
COPY . .

# Change ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port (if needed for health checks)
EXPOSE 3001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD node healthcheck.js || exit 1

# Run the application
CMD ["node", "main.js"]
