# Flux GitOps Setup for Materialize Azure Deployment

This guide explains how to set up Flux to automatically deploy Materialize updates from the MaterializeIncLabs repository.

## Prerequisites

- Flux installed on your AKS cluster
- Secrets manually created (since they use environment variable substitution)
- kubectl access to your cluster

## Option 1: Manual Secrets + Flux GitOps (Recommended)

This approach lets you manage secrets manually while having Flux handle the application deployment automatically.

### 1. Deploy Flux Resources

Apply the Flux configuration to watch the MaterializeIncLabs repository:

```bash
kubectl apply -f clusters/production/materialize/git-source.yaml
kubectl apply -f clusters/production/materialize/flux-kustomization.yaml
```

### 2. Create Secrets Manually

Since secrets use environment variable substitution for security, create them manually:

```bash
# Set up your environment
source .env

# Deploy secrets with substitution
envsubst < apps/materialize/postgres-secret.yaml | kubectl apply -f -
envsubst < apps/materialize/auth-secret.yaml | kubectl apply -f -
```

### 3. Verify Flux Deployment

```bash
# Check Flux is watching the repository
flux get sources git

# Check Flux deployment status
flux get kustomizations

# Monitor the deployment
kubectl get pods -n materialize-system -w
```

Now when you push changes to the MaterializeIncLabs repository, Flux will automatically:
- Pull the latest changes (every 1 minute)
- Apply any configuration updates (every 10 minutes)
- Health check the deployment
- Rollback on failures

## Option 2: Azure Key Vault + External Secrets (Production)

For production deployments, use Azure Key Vault with External Secrets Operator:

### 1. Install External Secrets Operator

```bash
helm repo add external-secrets https://charts.external-secrets.io
helm install external-secrets external-secrets/external-secrets -n external-secrets-system --create-namespace
```

### 2. Create Azure Key Vault

```bash
# Create Key Vault
az keyvault create \
  --name materialize-secrets-$(date +%s | tail -c 5) \
  --resource-group materialize-rg \
  --location eastus2

# Add secrets to Key Vault
az keyvault secret set --vault-name <your-keyvault> --name "postgres-host" --value "your-postgres-host.postgres.database.azure.com"
az keyvault secret set --vault-name <your-keyvault> --name "postgres-username" --value "your-username"
az keyvault secret set --vault-name <your-keyvault> --name "postgres-password" --value "your-password"
az keyvault secret set --vault-name <your-keyvault> --name "materialize-admin-password" --value "your-admin-password"
az keyvault secret set --vault-name <your-keyvault> --name "postgres-metadata-url" --value "postgresql://user:pass@host:5432/materialize?sslmode=require"
az keyvault secret set --vault-name <your-keyvault> --name "azure-blob-persist-url" --value "https://account.blob.core.windows.net/container?sas-token"
```

### 3. Configure Managed Identity

```bash
# Create managed identity for AKS
az identity create --name materialize-keyvault-identity --resource-group materialize-rg

# Get identity details
IDENTITY_CLIENT_ID=$(az identity show --name materialize-keyvault-identity --resource-group materialize-rg --query clientId -o tsv)
IDENTITY_RESOURCE_ID=$(az identity show --name materialize-keyvault-identity --resource-group materialize-rg --query id -o tsv)

# Assign AKS identity to use the managed identity
az aks pod-identity add --resource-group materialize-rg --cluster-name materialize-aks --namespace materialize-system --name materialize-keyvault-identity --identity-resource-id $IDENTITY_RESOURCE_ID

# Grant Key Vault access
az keyvault set-policy --name <your-keyvault> --spn $IDENTITY_CLIENT_ID --secret-permissions get list
```

### 4. Apply External Secrets Configuration

Update `clusters/production/materialize/external-secrets.yaml` with your Key Vault URL and apply:

```bash
kubectl apply -f clusters/production/materialize/external-secrets.yaml
```

## Flux Workflow

Once set up, your GitOps workflow will be:

1. **Make changes** to the MaterializeIncLabs repository
2. **Push to main** branch
3. **Flux detects changes** within 1 minute
4. **Flux applies updates** within 10 minutes
5. **Health checks verify** deployment success
6. **Rollback automatically** on failure

## Monitoring Flux

```bash
# Check source status
flux get sources git materialize-azure-gitops

# Check kustomization status
flux get kustomizations materialize

# Force reconciliation (manual trigger)
flux reconcile source git materialize-azure-gitops
flux reconcile kustomization materialize

# View logs
flux logs --level=info --all-namespaces
```

## Security Benefits

- **No secrets in Git**: All sensitive data in Key Vault or manually managed
- **Automatic updates**: Get latest Materialize features and security patches
- **Audit trail**: All changes tracked in Git
- **Rollback capability**: Automatic rollback on deployment failures
- **Drift detection**: Flux corrects manual cluster changes