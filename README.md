# Materialize GitOps Repository

This repository contains the GitOps configuration for deploying Materialize on Azure Kubernetes Service (AKS) using FluxCD.

## Structure

- `clusters/production/` - Production cluster configuration
- `apps/materialize/` - Materialize application manifests
- `clusters/production/flux-system/` - FluxCD system configuration

## Infrastructure

- **Azure Resource Group**: materialize-rg
- **AKS Cluster**: materialize-aks
- **PostgreSQL Server**: mz-postgres-1754509666.postgres.database.azure.com
- **Node Pools**: 
  - `nodepool1`: Standard_B2s (system workloads)
  - `mzpool`: Standard_E2pds_v6 with taint `materialize=dedicated:NoSchedule`

## Deployment

FluxCD will automatically deploy Materialize when changes are pushed to this repository.