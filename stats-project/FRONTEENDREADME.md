# Student statistics dashboard project Frontend

## Overview

React-based frontend for displaying arXiv usage statistics, featuring interactive charts and navigation. Built with React Router and Plotly.js.

This document is to be updated as it nears production-ready status.

## Prerequisites

- Node.js is all that is required to start setting up the frontend. 

## Relevant Files

### Core Components
- `App.js`: Main application router
- `StatsHome.js`: Landing page with category selection
- `StatsCategory.js`: Displays available charts for selected category
- `ChartDetail.js`: Renders specific chart components based on route

### Chart Components
- `DownloadsByArchive.js`: Total Downloads at Arxiv sorted by Archive
- `DownloadsByCategory.js`: Total Downloads at Arxiv sorted by Category, then Archive
- `DownloadsByCountry.js`: Total downloads by country, shown in a Tile Chloropleth Map
- `HourlyUsageRates.js`: Today's downloads by hour (timezone-aware)
- `MonthlyDownloads.js`: Monthly download totals over time, spanning from our founding to today
- `ChartContainer.js`: Reusable data fetching and chart rendering 
wrapper

### Configuration
- `HelmetConfig.js`: Handles page titles and stylesheets
- `index.js`: React application entry point


## Available Charts

### Download Statistics
- **Hourly Usage Rates**: Today's downloads by hour
- **Monthly Downloads**: Total downloads by month
- **Downloads by Country**: Geographic distribution
- **Downloads by Category**: Subject category breakdown
- **Downloads by Archive**: Archive-specific trends

### Submission Statistics
- TBD 

## Running the Application

### Development
1. First, install dependencies:
   ```bash
   npm install

2.  Then, start development server:
    ```bash
    npm start
    
3.  Access at  `http://localhost:3000`!
    

### Production Build

TBD