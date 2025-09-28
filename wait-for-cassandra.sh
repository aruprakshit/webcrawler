#!/bin/bash

# Wait for Cassandra to be ready
echo "Waiting for Cassandra to be ready..."
until cqlsh -e "SELECT now() FROM system.local;" > /dev/null 2>&1; do
  echo "Cassandra is not ready yet. Waiting..."
  sleep 2
done

echo "Cassandra is ready! Running schema initialization..."

# Run the schema file and capture the result
if cqlsh -f /app/cassandra-schema.sql; then
  echo "Schema initialization completed successfully!"
  exit 0
else
  echo "Schema initialization failed!"
  exit 1
fi
