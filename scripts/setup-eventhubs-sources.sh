#!/bin/bash

# Setup Event Hubs sources in Materialize
# This script uses environment variables for security

set -e

# Check required environment variables
if [[ -z "${EVENTHUBS_CONNECTION_STRING}" ]]; then
    echo "❌ Error: EVENTHUBS_CONNECTION_STRING environment variable not set"
    echo "Please source your .env file: source .env"
    exit 1
fi

if [[ -z "${EVENTHUBS_NAMESPACE}" ]]; then
    echo "❌ Error: EVENTHUBS_NAMESPACE environment variable not set"
    echo "Please source your .env file: source .env"
    exit 1
fi

if [[ -z "${MATERIALIZE_ADMIN_PASSWORD}" ]]; then
    echo "❌ Error: MATERIALIZE_ADMIN_PASSWORD environment variable not set"
    echo "Please source your .env file: source .env"
    echo "Note: This is required for RBAC-enabled Materialize authentication"
    exit 1
fi

echo "🔧 Setting up Event Hubs sources in Materialize..."
echo "📡 Event Hubs Namespace: ${EVENTHUBS_NAMESPACE}"

# Use port-forward to connect to Materialize
echo "🚀 Starting port-forward to Materialize..."
kubectl port-forward -n materialize-system svc/mzmpl79if4kx-environmentd 6875:6875 &
FORWARD_PID=$!
sleep 3

# Substitute environment variables and run SQL
echo "📝 Creating Event Hubs connection and sources..."
envsubst < scripts/setup-multi-topic-connection.sql | psql "postgresql://materialize:${MATERIALIZE_ADMIN_PASSWORD}@localhost:6875/materialize"

# Kill port-forward
kill $FORWARD_PID

echo "✅ Event Hubs sources setup complete!"
echo ""
echo "🔍 To test the setup:"
echo "  source .env"
echo "  python3 scripts/send-sample-data.py"
echo "  python3 scripts/send-more-updates.py"
echo ""
echo "📊 To query data:"
echo "  kubectl port-forward -n materialize-system svc/mzmpl79if4kx-environmentd 6875:6875 &"
echo "  psql \"postgresql://materialize:\${MATERIALIZE_ADMIN_PASSWORD}@localhost:6875/materialize\""