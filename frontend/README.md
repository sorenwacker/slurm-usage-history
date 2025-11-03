# Slurm Usage History - Frontend

Modern React + TypeScript frontend for the Slurm Usage History dashboard.

## Features

- **Interactive Dashboard**: Real-time visualization of cluster usage data
- **Advanced Filtering**: Filter by cluster, date range, partition, account, and job state
- **Multiple Visualizations**:
  - CPU/GPU usage over time
  - Job distribution by account
  - Job state breakdown
  - Summary statistics cards
- **Responsive Design**: Works on desktop and mobile devices
- **Fast and Modern**: Built with Vite, React 18, and TypeScript

## Setup

1. Install dependencies:
```bash
npm install
```

2. Configure the API endpoint:
```bash
cp .env.example .env
# Edit .env and set VITE_API_URL if needed (default: http://localhost:8000)
```

3. Start the development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:3100`

## Build for Production

```bash
npm run build
```

The built files will be in the `dist/` directory.

## Technology Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **TanStack Query** - Data fetching and caching
- **Plotly.js** - Interactive charts
- **Axios** - HTTP client

## Project Structure

```
frontend/
├── src/
│   ├── api/          # API client and endpoints
│   ├── components/   # Reusable UI components
│   ├── pages/        # Page components
│   ├── types/        # TypeScript type definitions
│   ├── utils/        # Utility functions
│   ├── App.tsx       # Main app component
│   └── main.tsx      # Entry point
├── public/           # Static assets
└── package.json      # Dependencies
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## Environment Variables

- `VITE_API_URL` - Backend API URL (default: http://localhost:8100)
