#!/bin/bash

# Enable RBAC authentication for Materialize
# This script deploys the authentication secret and restarts Materialize

set -e

echo "🔐 Enabling RBAC Authentication for Materialize"
echo "==============================================="

# Check required environment variables
if [[ -z "${MATERIALIZE_ADMIN_PASSWORD}" ]]; then
    echo "❌ Error: MATERIALIZE_ADMIN_PASSWORD environment variable not set"
    echo ""
    echo "Please set a strong admin password in your .env file:"
    echo "  export MATERIALIZE_ADMIN_PASSWORD=\"YourSecurePassword123!\""
    echo ""
    echo "Then source the file: source .env"
    exit 1
fi

echo "📋 Configuration:"
echo "  Admin Password: *** (${#MATERIALIZE_ADMIN_PASSWORD} characters)"
echo ""

# Deploy the authentication secret
echo "🔑 Deploying authentication secret..."
envsubst < apps/materialize/auth-secret.yaml | kubectl apply -f -

# Check if secret was created successfully
if kubectl get secret materialize-users -n materialize-system &>/dev/null; then
    echo "✅ Authentication secret created successfully"
else
    echo "❌ Failed to create authentication secret"
    exit 1
fi

echo ""
echo "🚀 RBAC has been enabled in the Materialize configuration."
echo "   The changes will take effect when Flux redeploys the environment."
echo ""
echo "📊 To connect to Materialize with authentication:"
echo "   kubectl port-forward -n materialize-system svc/mzmpl79if4kx-environmentd 6875:6875 &"
echo "   psql \"postgresql://materialize:\${MATERIALIZE_ADMIN_PASSWORD}@localhost:6875/materialize\""
echo ""
echo "⚠️  Note: If you encounter connection issues, you may need to increase"
echo "   PostgreSQL max_connections parameter:"
echo "   az postgres flexible-server parameter set \\"
echo "     --resource-group materialize-rg \\"
echo "     --server-name <your-postgres-server> \\"
echo "     --name max_connections \\"
echo "     --value 200"
echo ""
echo "✨ RBAC setup complete!"