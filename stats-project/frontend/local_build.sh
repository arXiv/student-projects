#!/bin/bash
# Holdover script from activity dashboard that does not work with this project.

export REACT_APP_API_Local_URL=http://localhost:8000
export REACT_APP_ENV=LOCAL

echo "Starting the React application..."
npm install
npm start