# Trading Chart Analyzer

## Overview
A web application that analyzes stock trading charts using AI-powered technical analysis. Users can upload chart screenshots and receive detailed buy/sell recommendations based on multiple technical indicators. The app also includes a trading history page to track performance over time.

## Features
- Upload trading chart images (PNG, JPG, JPEG, GIF, WebP)
- AI-powered chart analysis using Gemini
- Technical indicators analyzed:
  - Fibonacci retracement levels
  - RSI (Relative Strength Index)
  - MACD (Moving Average Convergence Divergence)
- Support and resistance level identification
- Entry and exit point suggestions
- Risk factor assessment
- Clear buy/sell/hold recommendations
- Trading history tracking with metrics:
  - Total trades, winning/losing trades, win rate
  - Date range and indicator type filters
  - Performance charts over time
  - Manual trade entry and editing

## Tech Stack
- **Backend**: Python 3.11, Flask, SQLAlchemy
- **Database**: PostgreSQL
- **AI**: Gemini AI (via Replit AI Integrations)
- **Image Processing**: OpenCV, Pillow
- **Frontend**: HTML, CSS, JavaScript, Chart.js

## Project Structure
```
├── app.py                 # Flask application entry point
├── chart_analyzer.py      # AI-powered chart analysis module
├── models.py              # SQLAlchemy database models
├── templates/
│   ├── index.html         # Main chart upload page
│   └── history.html       # Trading history page
├── static/
│   ├── style.css          # Styling
│   ├── app.js             # Chart upload JavaScript
│   └── history.js         # History page JavaScript
└── uploads/               # Temporary file uploads
```

## Running the Application
The app runs on port 5000. Start with:
```bash
python app.py
```

## Environment Variables
- `AI_INTEGRATIONS_GEMINI_API_KEY` - Automatically set by Replit AI Integrations
- `AI_INTEGRATIONS_GEMINI_BASE_URL` - Automatically set by Replit AI Integrations
- `DATABASE_URL` - PostgreSQL connection string

## API Endpoints
- `GET /` - Main chart analysis page
- `GET /history` - Trading history page
- `POST /analyze` - Analyze uploaded chart image
- `GET /api/trades` - Get all trades (with optional filters)
- `POST /api/trades` - Create new trade
- `PUT /api/trades/<id>` - Update trade
- `DELETE /api/trades/<id>` - Delete trade
- `GET /api/stats` - Get trading statistics

## Recent Changes
- December 28, 2025: Added trading history page with metrics, filters, and performance charts
- December 28, 2025: Initial creation of trading chart analyzer app

## User Preferences
- None specified yet
