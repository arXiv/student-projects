#!/bin/bash

# Set environment variables
#export REACT_APP_API_URL=https://services.dev.arxiv.org/activity
#export REACT_APP_ENV=DEV

# Build the Docker image, passing in the environment variables
#docker build --platform linux/amd64 -f Dockerfile \
  #--build-arg REACT_APP_API_URL=$REACT_APP_API_URL \
  #--build-arg REACT_APP_ENV=$REACT_APP_ENV \
  #-t stats_dashboard_front .

# Run the Docker container
#docker run -d -p 9000:9000 --name frontend_service stats_activity_dashboard_front

# Tag the Docker image
#docker tag stats_activity_dashboard_front gcr.io/arxiv-development/stats_activity_dashboard_front

# Push the Docker image to Google Container Registry
#docker push gcr.io/arxiv-development/stats_dashboard_front

#echo "Build and push completed successfully!"