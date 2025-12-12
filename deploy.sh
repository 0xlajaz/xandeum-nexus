#!/bin/bash

# Configuration variables
APP_NAME="xandeum-nexus-v7"
REGION="asia-southeast2" # Setting region for low latency access

echo "--- Starting Xandeum Nexus Deployment to Google Cloud Platform ---"

# 1. Authentication Check
echo "STATUS: Checking Google Cloud authentication status..."
# Suppress output of gcloud auth list to keep terminal clean
gcloud auth list &> /dev/null
if [ $? -ne 0 ]; then
    echo "WARNING: User is not logged in. Please run 'gcloud auth login' and try again."
    exit 1
fi

# 2. Get Project ID
PROJECT_ID=$(gcloud config get-value project)
echo "PROJECT: Using Project ID: $PROJECT_ID"

# 3. Enable Required Google Cloud Services
echo "SETUP: Enabling required APIs (Cloud Run and Cloud Build)..."
gcloud services enable run.googleapis.com \
    cloudbuild.googleapis.com \
    artifactregistry.googleapis.com

# 4. Deploy to Cloud Run (Build from Source)
echo "DEPLOY: Building and deploying container to Cloud Run (This may take 2-5 minutes)..."
gcloud run deploy $APP_NAME \
    --source . \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --port 8080 \
    --max-instances 10 \
    --memory 1Gi

# 5. Final Report and Status Check
if [ $? -eq 0 ]; then
    echo "------------------------------------------------------------------"
    echo "SUCCESS: DEPLOYMENT COMPLETE."
    SERVICE_URL=$(gcloud run services describe $APP_NAME --platform managed --region $REGION --format 'value(status.url)')
    echo "URL: Application is live at: $SERVICE_URL"
    echo "------------------------------------------------------------------"
else
    echo "ERROR: Deployment failed. Please check the Cloud Build logs for details."
fi