# Materialize GitOps with Azure Blob Storage

GitOps deployment of Materialize on Azure Kubernetes Service with Azure Blob Storage persistence.

## Architecture

- **Metadata Storage**: Azure PostgreSQL Flexible Server
- **Persistence Storage**: Azure Blob Storage with SAS token authentication
- **Deployment**: Flux GitOps with Helm charts
- **Security**: Environment variable substitution for sensitive data

## Prerequisites

- Azure Kubernetes Service (AKS) cluster
- Azure PostgreSQL Flexible Server
- Azure Storage Account with blob container
- kubectl configured for your cluster
- Flux installed (optional, for GitOps)

## Infrastructure Setup

### 1. Azure Resource Group
```bash
az group create --name materialize-rg --location eastus2
```

### 2. Azure PostgreSQL Flexible Server
```bash
# Create PostgreSQL server
az postgres flexible-server create \
  --resource-group materialize-rg \
  --name mz-postgres-$(date +%s) \
  --location eastus2 \
  --admin-user mzadmin \
  --admin-password "MaterializeDB123!" \
  --sku-name Standard_B1ms \
  --tier Burstable \
  --storage-size 32 \
  --version 14

# Create database
az postgres flexible-server db create \
  --resource-group materialize-rg \
  --server-name <your-postgres-server> \
  --database-name materialize

# Configure firewall (allow Azure services)
az postgres flexible-server firewall-rule create \
  --resource-group materialize-rg \
  --name <your-postgres-server> \
  --rule-name AllowAzureServices \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0
```

### 3. Azure Storage Account & Blob Container
```bash
# Create storage account
az storage account create \
  --name mzpersist$(date +%s | tail -c 5) \
  --resource-group materialize-rg \
  --location eastus2 \
  --sku Standard_LRS \
  --kind StorageV2

# Get storage account key
STORAGE_KEY=$(az storage account keys list \
  --account-name <your-storage-account> \
  --resource-group materialize-rg \
  --query "[0].value" -o tsv)

# Create blob container
az storage container create \
  --name materialize-persist \
  --account-name <your-storage-account> \
  --account-key $STORAGE_KEY
```

### 4. AKS Cluster with Dedicated Node Pool
```bash
# Create AKS cluster
az aks create \
  --resource-group materialize-rg \
  --name materialize-aks \
  --location eastus2 \
  --node-count 1 \
  --node-vm-size Standard_B2s \
  --generate-ssh-keys

# Add dedicated node pool for Materialize with taints
az aks nodepool add \
  --resource-group materialize-rg \
  --cluster-name materialize-aks \
  --name mzpool \
  --node-count 2 \
  --node-vm-size Standard_E2pds_v6 \
  --node-taints materialize=dedicated:NoSchedule \
  --labels agentpool=mzpool

# Get cluster credentials
az aks get-credentials \
  --resource-group materialize-rg \
  --name materialize-aks
```

## Quick Start

1. **Clone and configure**:
   ```bash
   git clone <this-repo>
   cd materialize-gitops
   cp .env.template .env
   # Edit .env with your values
   ```

2. **Deploy**:
   ```bash
   ./deploy.sh
   ```

3. **Access Materialize**:
   - Console: `http://<CONSOLE-IP>:8080`
   - SQL: `psql "postgresql://materialize@<SQL-IP>:6875/materialize"`

## Configuration

### Environment Variables (.env)

```bash
# PostgreSQL Configuration
export POSTGRES_HOST="your-postgres-host.postgres.database.azure.com"
export POSTGRES_USERNAME="your-username"
export POSTGRES_PASSWORD="your-password"

# Materialize Authentication
export MATERIALIZE_ADMIN_PASSWORD="your-admin-password"

# Azure Blob Storage Configuration
export AZURE_STORAGE_ACCOUNT="your-storage-account"
export AZURE_STORAGE_CONTAINER="your-container-name"
export AZURE_STORAGE_KEY="your-storage-key"
export AZURE_STORAGE_SAS_TOKEN="your-sas-token"
```

### Generating SAS Token

```bash
az storage account generate-sas \
  --account-name YOUR-STORAGE-ACCOUNT \
  --account-key YOUR-STORAGE-KEY \
  --services b \
  --resource-types sco \
  --permissions rwdlacup \
  --expiry 2026-12-31 \
  --https-only
```

## Components

### Core Files
- `apps/materialize/environment.yaml` - Materialize environment configuration
- `apps/materialize/postgres-secret.yaml` - Database credentials (templated)
- `apps/materialize/helm-release.yaml` - Helm chart configuration
- `apps/materialize/external-access.yaml` - LoadBalancer services

### Security
- Sensitive data secured via environment variables
- SAS token authentication for blob storage
- Network policies for pod-to-pod communication
- SSL/TLS for database connections

### Persistence Architecture
- **Metadata**: PostgreSQL stores system catalogs, user management, and cluster state
- **Data**: Azure Blob Storage stores all table data, indexes, and materialized views
- **Separation**: Clean separation allows scaling storage independently

## Monitoring

```bash
# Pod status
kubectl get pods -n materialize-system

# Service endpoints
kubectl get svc -n materialize-system

# Logs
kubectl logs -n materialize-system <pod-name>

# Blob storage usage
az storage blob list --account-name <account> --container-name <container>
```

## Testing the Deployment

### 1. Verify Materialize Connection
```bash
kubectl run test-materialize --image=postgres:15 --restart=Never --rm -- \
  bash -c "psql 'postgresql://materialize@<SERVICE-IP>:6875/materialize' -c 'SELECT 1 as test;'"
```

### 2. Create Test Data
```bash
kubectl run test-materialize --image=postgres:15 --restart=Never --rm -- \
  bash -c "psql 'postgresql://materialize@<SERVICE-IP>:6875/materialize' <<EOF
CREATE TABLE test_data (id INT, name TEXT);
INSERT INTO test_data VALUES (1, 'blob-test-data'), (2, 'azure-storage');
SELECT * FROM test_data;
EOF"
```

### 3. Verify Blob Storage Persistence
```bash
# Check blob files created
az storage blob list \
  --account-name <your-storage-account> \
  --container-name materialize-persist \
  --account-key <your-storage-key> \
  --output table
```

You should see hundreds of blob files with names like:
- `s<shard-id>/v<version>/r<record-id>` - Data persistence files
- `s<shard-id>/n<node>/p<partition>` - Partition data files

## Troubleshooting

### Common Issues

1. **Pod CrashLoopBackOff**
   - Check PostgreSQL connectivity
   - Verify blob storage credentials
   - Review environment variables

2. **No Service Endpoints**
   - Pod may still be initializing
   - Check logs for startup errors

3. **Authentication Errors**
   - Verify SAS token is valid and not expired
   - Check PostgreSQL credentials

4. **Node Scheduling Issues**
   - Ensure tainted nodes exist: `kubectl get nodes -o wide`
   - Check tolerations match taints

### Environment Recreation

If you need to start fresh with blob storage (e.g., after configuration changes):

1. **Generate new environment ID**:
   ```bash
   uuidgen | tr '[:upper:]' '[:lower:]'
   # Update environment.yaml with new environmentId
   ```

2. **Clear blob storage** (optional):
   ```bash
   az storage blob delete-batch \
     --source materialize-persist \
     --account-name <account> \
     --account-key <key>
   ```

## Security Notes

- Never commit `.env` file to git
- Rotate SAS tokens regularly
- Use least privilege access for PostgreSQL user
- Consider Azure Key Vault for production secrets
- Restrict network access in production (remove 0.0.0.0/0 CIDRS)
- Change default passwords before production use

## Cost Optimization

- **Storage**: Use LRS replication for non-critical data
- **Compute**: Consider smaller node sizes for development
- **PostgreSQL**: Use Burstable tier for variable workloads
- **Blob Storage**: Consider archival tiers for old data

## Contributing

1. Test changes in development environment
2. Update environment variables as needed
3. Verify deployment with `./deploy.sh`
4. Submit PR with description of changes