# Google Cloud Run Installation Guide

Deploy MediaGrand on Google Cloud Run for optimal scaling and cost-effectiveness. This guide will help you set up your environment quickly and efficiently.

## Prerequisites

- Google Cloud account ([Sign up](https://cloud.google.com/))
- Basic familiarity with GCP Console
- `gcloud` CLI (optional but recommended)

## Quick Setup Steps

### 1. Project Setup

```bash
# Create new project (via CLI)
gcloud projects create mediagrand-project

# Or use GCP Console:
# 1. Open 'Select Project' dropdown
# 2. Click 'New Project'
# 3. Name it 'mediagrand-project'
```

### 2. Enable Required APIs

From GCP Console > APIs & Services > Enable APIs:
- Cloud Run API
- Cloud Storage API
- Cloud Build API

### 3. Create Storage Bucket

```bash
# Via CLI
gcloud storage buckets create gs://mediagrand-media

# Or via Console:
# Storage > Create Bucket
# Name: mediagrand-media
# Location: Choose nearest region
# Access Control: Uniform
```

### 4. Set Up Service Account

```bash
# Create service account
gcloud iam service-accounts create mediagrand-service \
  --display-name="MediaGrand Service Account"

# Grant permissions
gcloud projects add-iam-policy-binding mediagrand-project \
  --member="serviceAccount:mediagrand-service@mediagrand-project.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

# Download key
gcloud iam service-accounts keys create key.json \
  --iam-account=mediagrand-service@mediagrand-project.iam.gserviceaccount.com
```

### 5. Deploy to Cloud Run

```bash
# Deploy service
gcloud run deploy mediagrand \
  --image=isaacgounton/mediagrand:latest \
  --platform=managed \
  --memory=16Gi \
  --cpu=4 \
  --port=8080 \
  --allow-unauthenticated \
  --set-env-vars="API_KEY=your-api-key" \
  --set-env-vars="GCP_BUCKET_NAME=mediagrand-media" \
  --set-env-vars="GCP_SA_CREDENTIALS=$(cat key.json | tr -d '\n')"
```

## Configuration Options

### Resource Allocation

```yaml
Memory: 16 GB (Recommended)
CPU: 4 (Adjustable)
Minimum Instances: 0
Maximum Instances: 5 (Adjust based on load)
```

### Environment Variables

```bash
API_KEY=your-secure-key
GCP_BUCKET_NAME=mediagrand-media
GCP_SA_CREDENTIALS='{contents-of-key.json}'
```

## Performance Optimization

### Request Handling
- Set timeout to 300s for long-running operations
- Enable CPU always allocated for consistent performance
- Use startup boost for faster cold starts

### Scaling Settings
- Set min instances to 0 to minimize costs
- Adjust max instances based on traffic patterns
- Monitor CPU/memory usage to fine-tune resources

## Troubleshooting

### Common Issues

1. **Deployment Failures**
   ```bash
   # Check service status
   gcloud run services describe mediagrand
   ```

2. **Permission Errors**
   ```bash
   # Verify service account roles
   gcloud projects get-iam-policy mediagrand-project
   ```

3. **Memory/CPU Issues**
   ```bash
   # View service metrics
   gcloud run services describe mediagrand --format='yaml(status)'
   ```

### Health Checks

Monitor your deployment:
- Cloud Run dashboard
- Cloud Monitoring metrics
- Cloud Logging for errors

## Testing

1. Get your service URL:
```bash
gcloud run services describe mediagrand --format='value(status.url)'
```

2. Test an endpoint:
```bash
curl -X POST "${SERVICE_URL}/v1/toolkit/test" \
  -H "x-api-key: your-api-key" \
  -H "Content-Type: application/json"
```

## Next Steps

- Set up Cloud Monitoring alerts
- Configure custom domains
- Implement CI/CD pipelines

Need help? Join our [MediaGrand Community](https://www.skool.com/no-code-architects) for support.
