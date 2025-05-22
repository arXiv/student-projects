#!/bin/bash

export REACT_APP_API_Local_URL=http://localhost:8000
export REACT_APP_ENV=LOCAL

echo "Starting the React application..."
npm install
npm start