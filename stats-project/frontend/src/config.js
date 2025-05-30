// src/config.js
// This file contains configuration settings for the frontend application, fetching our API base URL from environment variables or defaulting to a local server.
export const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8080/api';