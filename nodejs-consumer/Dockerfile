FROM node:24-alpine

# Create non-root user with UID/GID 1001 (avoiding system user 1000)
RUN addgroup -g 1001 appuser && \
  adduser -D -u 1001 -G appuser appuser

# Set working directory
WORKDIR /app

# Copy package.json first for better layer caching
COPY package.json ./

# Install dependencies as root (before copying source code)
RUN npm install --omit=dev && npm cache clean --force

# Copy application code
COPY . .

# Change ownership to non-root user (after all files are copied)
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port (if needed for health checks)
EXPOSE 3001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD node healthcheck.js || exit 1

# Run the application
CMD ["node", "src/main.js"]
