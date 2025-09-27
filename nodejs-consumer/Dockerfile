FROM node:24-alpine

# Create non-root user with UID/GID 1001 (avoiding system user 1000)
RUN addgroup -g 1001 appuser && \
  adduser -D -u 1001 -G appuser appuser

# Set working directory
WORKDIR /app

# Copy package.json only
COPY package.json ./

# Copy application code
COPY . .

# Change ownership to non-root user first
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Install dependencies as non-root user
RUN npm install --omit=dev && npm cache clean --force

# Expose port (if needed for health checks)
EXPOSE 3001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD node healthcheck.js || exit 1

# Run the application
CMD ["node", "main.js"]
