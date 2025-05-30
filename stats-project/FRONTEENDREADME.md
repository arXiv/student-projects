
# Student statistics dashboard project Frontend

  

## Overview

  

React-based frontend for displaying arXiv usage statistics, featuring interactive charts and navigation. Built with React Router and Plotly.js, and intended to be used with the stats API within this same repository.

  

This document is to be updated as it nears production-ready status.

  

## Prerequisites

  

- Node.js and NPM is all that is required to start setting up the frontend.

  

## Relevant Files

  

### Core Components

-  `App.js`: Main application router

-  `StatsHome.js`: Landing page with category selection

-  `StatsCategory.js`: Displays available charts for selected category

-  `ChartDetail.js`: Renders specific chart components based on route

  

### Chart Components

-  `DownloadsByArchive.js`: Total Downloads at Arxiv sorted by Archive

-  `DownloadsByCategory.js`: Total Downloads at Arxiv sorted by Category, then Archive

-  `DownloadsByCountry.js`: Total downloads by country, shown in a Tile Chloropleth Map

-  `HourlyUsageRates.js`: Today's downloads by hour (timezone-aware)

-  `MonthlyDownloads.js`: Monthly download totals over time, spanning from our founding to today

-  `ChartContainer.js`: Reusable data fetching and chart rendering

wrapper

  

### Configuration

-  `HelmetConfig.js`: Handles page titles and stylesheets
-  `index.js`: React application entry point
- `config.js`: Gathers environment variables to build the API URL to request data from. 

  
  

## Available Charts

  

### Download Statistics

-  **Daily Usage Rates**: Downloads by hour every day, defaulting to user or UTC time zone. Can navigate to any given point we have data. 

-  **Monthly Downloads**: Total downloads by month over all time.

-  **Downloads by Country**: Geographic distribution of downloads over all time.

-  **Downloads by Category**: Category-specific download numbers over all time.

-  **Downloads by Archive**: Archive-specific download numbers over all time.

  

### Submission Statistics

- TBD

  

## Running the Application

  

### Locally

1. First, install dependencies:

```bash
npm install
```

2. Go to the frontend folder, and specify your API's base URL: 
```
REACT_APP_API_BASE_URL=https:/i-am-a-api-link
```
4. Then, start the development server:

```bash 
npm start
```

3. Access at `http://localhost:3000`!

  

### Containerizing

1.  **Build the Docker image**, giving it a build argument of your API base URL
    
    ```docker  build  --build-arg  REACT_APP_API_BASE_URL=https:/i-am-a-api-link  -t  stats-dashboard-front .```
    
2.  **Run the container**, mapping port 9000:
    
    ```docker  run  -p  9000:9000  my-frontend```
    
3.  **Access the app**  at  http://localhost:9000  in your browser. You might need to give it a second to cook.
    



  

## Known Issues / WIPs
1. Without access to submission statistics the submissions category of the frontend merely routes the user to our current (and possibly outdated) submissions stats page. 
2. If something goes awry on a given page the UI wrapped around our graph will begin to break away...
3. Configuration between local/development/production builds unfinished.
4. Formal production worthy build unfinished. 