# RADAR Frontend Analysis

## Overview
The frontend is a Next.js application with TypeScript that provides a sophisticated search interface with AI-powered filtering, dynamic columns, automation, and export capabilities.

## Key Components Structure

### Main Page (`app/page.tsx`)
- **SearchResult Interface**: 
  ```typescript
  interface SearchResult {
    id: string
    title: string
    url: string
    country: string
    language: string
    date: string
    category: string
    status: string
    source: string
    score: number
  }
  ```

### Authentication (`components/auth-provider.tsx`)
- Uses localStorage for authentication state
- Simple email-based login (no password validation in frontend)
- Redirects between `/landing` and main app based on auth status

## API Endpoints Expected by Frontend

### 1. POST /ai-search
**Purpose**: AI-powered search with automatic filter generation
**Request Body**:
```json
{
  "query": "string",
  "create_filters": true
}
```
**Response**:
```json
{
  "results": [SearchResult[]],
  "filters": {
    "country": "string",
    "language": "string", 
    "category": "string",
    "status": "string"
  }
}
```

### 2. GET /search
**Purpose**: Standard search with query parameters
**Query Parameters**:
- `q`: search query
- `page`: page number
- `page_size`: results per page
- `country`: filter by country (optional)
- `language`: filter by language (optional)
- `category`: filter by category (optional)
- `state`: filter by status (optional)

**Response**:
```json
{
  "results": [SearchResult[]]
}
```

### 3. PUT /items/{id}
**Purpose**: Update individual search result fields
**Request Body**:
```json
{
  "[field_name]": "new_value"
}
```

### 4. POST /jobs
**Purpose**: Schedule automated searches
**Request Body**:
```json
{
  "query": "string",
  "interval": "24h|weekly|monthly",
  "filters": {...}
}
```

## Frontend Features Analysis

### Search Functionality
- Natural language search input
- Real-time AI filter generation based on query
- Progress indicators with status messages
- Mock data shows 70-second search simulation

### Filter System
- **Basic Filters**: Country, Language, Category, Status
- **AI-Generated Filters**: Automatically created from search query
- **Advanced Filters**: Location, status, category, source
- **Custom Filters**: User-defined filter criteria

### Results Table
- Editable cells (inline editing)
- Sortable columns
- Resizable columns
- Pagination (10, 25, 50, 100 results per page)
- Custom column creation with AI assistance

### Dynamic Columns
- Users can add custom columns
- AI can suggest and populate column data
- Column data generation based on search results
- History/undo functionality for column changes

### Export Functionality
- PDF export with jsPDF
- Excel export with XLSX library
- Configurable export options

### Automation
- Schedule searches at intervals (24h, weekly, monthly)
- Notification system for new results
- Saved search configurations

## Environment Configuration
- Uses `NEXT_PUBLIC_API_URL` environment variable
- Falls back to mock data when API URL not set
- Currently deployed on Vercel

## Authentication Flow
- Landing page (`/landing`) for unauthenticated users
- Login page (`/login`) with email input
- Main app (`/`) for authenticated users
- Simple localStorage-based session management

## UI/UX Patterns
- Dark theme with green accent color (`primary`)
- Responsive design with mobile support
- Loading states and progress indicators
- Toast notifications for user feedback
- Modal dialogs for complex interactions

## Key Dependencies
- Next.js 14 with TypeScript
- Tailwind CSS for styling
- Radix UI components
- Lucide React icons
- jsPDF and XLSX for exports
- React Hook Form for form handling

## Backend Implementation Requirements

Based on this analysis, the backend needs to implement:

1. **Database Models**: Users, Searches, Results, Columns, Column Values, Automations
2. **Search Integration**: Google Custom Search, Bing, NewsAPI, Common Crawl
3. **AI Integration**: OpenAI API for query interpretation and filter generation
4. **Background Tasks**: Celery + Redis for automated searches
5. **Export Services**: PDF and Excel generation endpoints
6. **Authentication**: Simple email-based auth matching frontend expectations

## Mock Data Structure
The frontend currently uses mock data with 10 sample results covering various categories (Technology, Finance, Environment, Health, Science, Education) and countries (USA, UK, DE, CA, JP, FR, ES, FI, IL).
