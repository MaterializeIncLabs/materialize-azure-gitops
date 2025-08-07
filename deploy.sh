#!/bin/bash
# Materialize GitOps Deployment Script

set -e

echo "🚀 Deploying Materialize with Azure Blob Storage persistence"
echo

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found"
    echo "📝 Copy .env.template to .env and fill in your values"
    exit 1
fi

# Source environment variables
echo "🔧 Loading environment variables..."
source .env

# Verify required variables are set
required_vars=("POSTGRES_HOST" "POSTGRES_USERNAME" "POSTGRES_PASSWORD" "AZURE_STORAGE_ACCOUNT" "AZURE_STORAGE_CONTAINER" "AZURE_STORAGE_SAS_TOKEN")

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Error: $var is not set in .env file"
        exit 1
    fi
done

echo "✅ All required environment variables are set"
echo

# Deploy components
echo "📦 Deploying Materialize components..."

cd apps/materialize

# Deploy static components first
kubectl apply -f namespace.yaml
kubectl apply -f helm-repository.yaml
kubectl apply -f helm-release.yaml
kubectl apply -f external-access.yaml
kubectl apply -f security.yaml

# Deploy templated secrets with environment variable substitution
echo "🔐 Deploying secrets with environment variable substitution..."
envsubst < postgres-secret.yaml | kubectl apply -f -
envsubst < auth-secret.yaml | kubectl apply -f -

# Deploy Materialize environment
kubectl apply -f environment.yaml

echo
echo "✅ Deployment complete!"
echo
echo "📊 Console URL: http://$(kubectl get svc materialize-console-external -n materialize-system -o jsonpath='{.status.loadBalancer.ingress[0].ip}'):8080"
echo "🔗 SQL Connection: $(kubectl get svc materialize-sql-external -n materialize-system -o jsonpath='{.status.loadBalancer.ingress[0].ip}'):6875"
echo
echo "🔍 Monitor deployment status:"
echo "kubectl get pods -n materialize-system -w"