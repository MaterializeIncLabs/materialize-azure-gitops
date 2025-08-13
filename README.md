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
  --admin-password "password!" \
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
   - SQL (with RBAC): `psql "postgresql://materialize:${MATERIALIZE_ADMIN_PASSWORD}@<SQL-IP>:6875/materialize"`

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

## RBAC Authentication

This deployment enables Role-Based Access Control (RBAC) for secure access to Materialize.

### Setup Authentication

#### 1. Configure Admin Password
```bash
# Edit your .env file with a strong password
export MATERIALIZE_ADMIN_PASSWORD="YourSecurePassword123!"
source .env
```

#### 2. Deploy Authentication Secret
```bash
# Create the authentication secret with your password
envsubst < apps/materialize/auth-secret.yaml | kubectl apply -f -
```

#### 3. Verify RBAC Configuration
The Materialize environment is configured with:
- `enableRbac: true` - RBAC enabled
- `authenticatorKind: Password` - Password authentication
- License key required for RBAC features

### Connecting with Authentication

#### Via Port-Forward
```bash
kubectl port-forward -n materialize-system svc/mzmpl79if4kx-environmentd 6875:6875 &
psql "postgresql://materialize:${MATERIALIZE_ADMIN_PASSWORD}@localhost:6875/materialize"
```

#### Via Load Balancer
```bash
# Get the external IP
kubectl get svc -n materialize-system materialize-sql-external

# Connect with authentication
psql "postgresql://materialize:${MATERIALIZE_ADMIN_PASSWORD}@<EXTERNAL-IP>:6875/materialize"
```

### User Management

Once connected as admin, you can create additional users:
```sql
-- Create a new user
CREATE ROLE analyst LOGIN PASSWORD 'analyst_password';

-- Grant permissions
GRANT SELECT ON ALL TABLES IN SCHEMA public TO analyst;
GRANT SELECT ON ALL MATERIALIZED VIEWS IN SCHEMA public TO analyst;

-- Connect as the new user
psql "postgresql://analyst:analyst_password@<host>:6875/materialize"
```

### Troubleshooting RBAC

**Connection Refused**: Check PostgreSQL connection limits
```bash
# Increase max_connections if needed
az postgres flexible-server parameter set \
  --resource-group materialize-rg \
  --server-name <postgres-server> \
  --name max_connections \
  --value 200
```

**Authentication Failed**: Verify secret deployment
```bash
# Check if secret exists and has correct values
kubectl get secret materialize-users -n materialize-system -o yaml
```

**DNS Resolution Issues**: If RBAC pods fail with "Name or service not known"
```bash
# Ensure postgres-credentials secret has actual values, not template variables
kubectl get secret postgres-credentials -n materialize-system -o jsonpath='{.data.metadata_backend_url}' | base64 -d
# Should show: postgresql://user:pass@host:5432/materialize?sslmode=require
# NOT: postgresql://${POSTGRES_USERNAME}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:5432/materialize
```

**Missing License Key**: If pods crash with "failed to validate license key"
```bash
# Verify license_key exists in postgres-credentials secret
kubectl get secret postgres-credentials -n materialize-system -o jsonpath='{.data.license_key}' | base64 -d | wc -c
# Should return a large number (license key length), not 0
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
# Get admin password from environment
source .env

# Test connection with authentication
kubectl run test-materialize --image=postgres:15 --restart=Never --rm -it -- \
  bash -c "psql 'postgresql://materialize:${MATERIALIZE_ADMIN_PASSWORD}@<SERVICE-IP>:6875/materialize' -c 'SELECT 1 as test;'"
```

### 2. Create Test Data
```bash
# Create test data with authentication
kubectl run test-materialize --image=postgres:15 --restart=Never --rm -it -- \
  bash -c "psql 'postgresql://materialize:${MATERIALIZE_ADMIN_PASSWORD}@<SERVICE-IP>:6875/materialize' <<EOF
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

## Azure Event Hubs Integration

This setup includes Azure Event Hubs for real-time data streaming into Materialize. The integration supports both append-only and upsert data patterns.

### Event Hubs Infrastructure

#### 1. Create Event Hubs Namespace
```bash
az eventhubs namespace create \
  --resource-group materialize-rg \
  --name mz-eventhubs-$(date +%s | tail -c 8) \
  --location eastus2 \
  --sku Standard
```

#### 2. Create Event Hub Topics
```bash
# Orders topic (append-only)
az eventhubs eventhub create \
  --resource-group materialize-rg \
  --namespace-name <your-eventhubs-namespace> \
  --name orders \
  --partition-count 4

# Customers topic (upsert)
az eventhubs eventhub create \
  --resource-group materialize-rg \
  --namespace-name <your-eventhubs-namespace> \
  --name customers \
  --partition-count 2
```

#### 3. Create Namespace-Level Authorization Rules
```bash
# Read access for Materialize (all topics)
az eventhubs namespace authorization-rule create \
  --resource-group materialize-rg \
  --namespace-name <your-eventhubs-namespace> \
  --name materialize-multi-reader \
  --rights Listen

# Write access for data publishers (all topics)
az eventhubs namespace authorization-rule create \
  --resource-group materialize-rg \
  --namespace-name <your-eventhubs-namespace> \
  --name data-multi-publisher \
  --rights Send

# Get connection strings
az eventhubs namespace authorization-rule keys list \
  --resource-group materialize-rg \
  --namespace-name <your-eventhubs-namespace> \
  --name materialize-multi-reader
```

### Materialize Configuration

#### 1. Create Single Connection for Multiple Topics
```sql
-- Create secret with namespace-level connection (no EntityPath)
CREATE SECRET eventhubs_namespace_connection AS '<your-connection-string>';

-- Create single Kafka connection for all Event Hub topics
CREATE CONNECTION eventhubs_multi_kafka TO KAFKA (
    BROKER '<your-namespace>.servicebus.windows.net:9093',
    SASL MECHANISMS = 'PLAIN',
    SASL USERNAME = '$ConnectionString',
    SASL PASSWORD = SECRET eventhubs_namespace_connection,
    SECURITY PROTOCOL = 'SASL_SSL'
);
```

#### 2. Create Sources

**Orders (Append-Only)**
```sql
CREATE SOURCE orders_raw
FROM KAFKA CONNECTION eventhubs_multi_kafka (TOPIC 'orders')
FORMAT JSON;

CREATE MATERIALIZED VIEW orders AS
SELECT
    (data->>'order_id')::text as order_id,
    (data->>'customer_name')::text as customer_name,
    (data->>'total_amount')::double as total_amount,
    (data->>'status')::text as status,
    (data->>'created_at')::text as created_at,
    (data->>'region')::text as region
FROM orders_raw;
```

**Customers (Upsert)**
```sql
CREATE SOURCE customers_raw
FROM KAFKA CONNECTION eventhubs_multi_kafka (TOPIC 'customers')
KEY FORMAT TEXT
VALUE FORMAT JSON
ENVELOPE UPSERT;

CREATE MATERIALIZED VIEW customers AS
SELECT
    (data->>'customer_id')::text as customer_id,
    (data->>'first_name')::text as first_name,
    (data->>'last_name')::text as last_name,
    (data->>'tier')::text as tier,
    (data->>'total_orders')::int as total_orders,
    (data->>'lifetime_value')::double as lifetime_value
FROM customers_raw
WHERE data IS NOT NULL;
```

### Setup Event Hubs Integration

#### 1. Configure Environment Variables
```bash
# Copy template and edit with your values
cp .env.template .env
# Edit .env with your Event Hubs namespace and connection strings

# Load environment
source .env
```

#### 2. Setup Materialize Sources
```bash
# Automatically create Event Hubs connection and sources
./scripts/setup-eventhubs-sources.sh
```

#### 3. Send Test Data
```bash
# Send sample orders (append-only)
python3 scripts/send-sample-data.py

# Send customer updates (demonstrates upsert)
python3 scripts/send-more-updates.py
```

#### 4. Query Real-time Data
```sql
-- Check orders stream
SELECT COUNT(*) FROM orders;
SELECT * FROM orders ORDER BY created_at DESC LIMIT 10;

-- Check customer upserts (should show latest state only)
SELECT COUNT(*) FROM customers;  -- Exactly 10 customers despite multiple updates
SELECT * FROM customers ORDER BY lifetime_value DESC;

-- Real-time analytics
SELECT region, COUNT(*) as orders, SUM(total_amount) as revenue
FROM orders GROUP BY region;

SELECT tier, AVG(total_orders) as avg_orders, SUM(lifetime_value) as total_ltv
FROM customers GROUP BY tier;
```

### Event Hubs Benefits

- **Real-time Streaming**: Sub-second latency from Event Hubs to Materialize
- **Single Connection**: One connection serves multiple topics (cost-efficient)
- **Kafka Compatibility**: Event Hubs speaks Kafka protocol natively
- **Upsert Support**: Proper key-based upserts for maintaining current state
- **Scalability**: Partitioned topics for high throughput
- **Persistence**: Event retention for replay and recovery

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

- **Never commit `.env` file to git** - contains sensitive credentials
- All scripts use environment variables - no hardcoded secrets
- Rotate SAS tokens and Event Hubs access keys regularly
- Use namespace-level Event Hubs authorization for multi-topic access
- Use least privilege access for PostgreSQL user
- Consider Azure Key Vault for production secrets
- Restrict network access in production (remove 0.0.0.0/0 CIDRS)
- Change default passwords before production use
- Event Hubs connection strings should have minimal required permissions (Listen/Send only)

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
