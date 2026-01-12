---
title: StageMasterAI Virtual Staging App MVP Design Plan
author: Architect Mode
date: 2026-01-11
status: draft
related_issue: design_prompt.txt
---

# AI Virtual Staging App - MVP Design Plan

## Executive Summary

This document outlines the MVP design for an AI-powered virtual staging application tailored for real estate agents. The product enables agents to upload interior photos and receive photorealistically staged images within minutes, optimized for property listing use.

**Photography-Style Theme**: The UI design draws inspiration from professional photography software (Adobe Lightroom, Capture One, Luminar), creating a familiar and premium experience for users who approach virtual staging with a photographer's mindset.

**Local Development Focus**: This app is designed to run entirely locally using Docker, including storage (MinIO) and configurable AI inference endpoints.

## 1. Product Goals & Success Metrics

### Primary Goal (MVP)
Enable real estate agents to transform empty room photos into professionally staged interiors using AI, reducing the time and cost of traditional home staging.

### Key Success Metrics
- **Generation Time**: Complete staging within 3-5 minutes
- **Success Rate**: 95% successful generations on first attempt
- **User Satisfaction**: 4+ star rating from agents
- **Compliance**: 100% adherence to disclosure requirements
- **System Uptime**: 99.5% availability

## 2. Core Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER WORKFLOW FLOW                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐ │
│  │  IMPORT  │───▶│  SELECT  │───▶│ RENDER   │───▶│ PREVIEW  │
│  │   PHOTO  │    │   ROOM   │    │          │    │   RESULT │
│  └──────────┘    │   STYLE  │    └──────────┘    └──────────┘ │
│                  └──────────┘           │                      │
│                                          ▼                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    EXPORT STAGED IMAGE                   │  │
│  │         (with virtual staging disclosure label)          │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Detailed Steps
1. **Import Photo**: User drags/drops or selects interior image (max 25MB, JPG/PNG)
2. **Select Room Type**: Living Room, Bedroom, Kitchen, Dining Room, Office, etc.
3. **Choose Style Presets**: 3-5 predefined styles (Modern, Traditional, Minimalist, etc.)
4. **Render**: Queue job, show rendering progress with time estimates
5. **Preview Result**: Before/after comparison with metadata panel
6. **Export**: Download with auto-applied compliance label

## 3. Local Development Architecture

### Docker-Based Local Stack

```mermaid
flowchart TB
    subgraph Local["Local Development - Docker Compose"]
        subgraph Frontend["Frontend Container"]
            REACT["React + Vite + Tailwind"]
        end
        
        subgraph Backend["Backend Container"]
            FASTAPI["FastAPI Application"]
        end
        
        subgraph Worker["Worker Container"]
            WORKER["Async Worker - RQ"]
        end
        
        subgraph Storage["Storage Containers"]
            MINIO["MinIO S3-Compatible Storage"]
            POSTGRES["PostgreSQL Database"]
            REDIS["Redis Queue & Cache"]
        end
        
        subgraph AI["AI Service - OpenRouter"]
            OPENROUTER["OpenRouter API"]
        end
        
        REACT -->|"API Calls"| FASTAPI
        FASTAPI -->|"Read/Write"| POSTGRES
        FASTAPI -->|"Upload/Download"| MINIO
        FASTAPI -->|"Job Queue"| REDIS
        REDIS --> WORKER
        WORKER -->|"Store Results"| MINIO
        WORKER -->|"Metadata"| POSTGRES
        WORKER -->|"AI Inference"| OPENROUTER
    end
```

### Local Development Services

| Service | Docker Image | Local Port | Purpose |
|---------|--------------|------------|---------|
| Frontend | Node.js 18 + Vite | http://localhost:3000 | React SPA |
| Backend | Python 3.12 + FastAPI | http://localhost:8000 | REST API |
| MinIO | minio/minio | http://localhost:9000 | S3-compatible storage |
| PostgreSQL | postgres:15 | localhost:5432 | Metadata database |
| Redis | redis:7-alpine | localhost:6379 | Job queue & caching |

### Local Storage Configuration

**MinIO Setup:**
```bash
# MinIO Console: http://localhost:9001
# Access Key: minioadmin
# Secret Key: minioadmin

# Create buckets:
# - stage-uploads (original images)
# - stage-results (staged images)
# - stage-thumbnails (preview images)
```

**Environment Variables for Local Development:**
```bash
# .env.local
STORAGE_ENDPOINT=localhost:9000
STORAGE_ACCESS_KEY=minioadmin
STORAGE_SECRET_KEY=minioadmin
STORAGE_BUCKET_UPLOADS=stage-uploads
STORAGE_BUCKET_RESULTS=stage-results
STORAGE_BUCKET_THUMBNAILS=stage-thumbnails
STORAGE_USE_SSL=false

DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/stage_db
REDIS_URL=redis://localhost:6379/0

AI_SERVICE_URL=http://localhost:8001  # Local inference endpoint (optional)
AI_SERVICE_TYPE=local  # or "replicate", "openai"
```

## 4. System Architecture

### High-Level Architecture

```mermaid
flowchart TB
    subgraph Frontend["Frontend Layer - React Vite Tailwind"]
        UI["React SPA"]
    end
    
    subgraph Backend["Backend Layer - FastAPI"]
        API["REST API"]
        WS["WebSocket"]
    end
    
    subgraph Worker["Worker Layer - Async Processing"]
        Q["Redis Queue"]
        WORKER["Async Worker"]
        AI["AI Generation"]
    end
    
    subgraph Storage["Storage Layer - Local Docker"]
        S3["MinIO S3 Storage"]
        DB["PostgreSQL"]
        CACHE["Redis Cache"]
    end
    
    UI -->|"Upload/Download"| API
    API -->|"Job Queue"| Q
    Q --> WORKER
    WORKER -->|"Generate"| AI
    WORKER -->|"Status Updates"| WS
    WS -->|"Real-time"| UI
    WORKER -->|"Store Results"| S3
    WORKER -->|"Metadata"| DB
    API -->|"Job Status"| CACHE
    API -->|"Read/Write"| DB
    API -->|"Store Files"| S3
```

### Component Details

#### Frontend (React + Vite + Tailwind)
```
frontend/
├── src/
│   ├── components/
│   │   ├── Landing/
│   │   │   ├── HeroSection.jsx
│   │   │   ├── FeaturesSection.jsx
│   │   │   ├── BeforeAfterSection.jsx
│   │   │   ├── PricingSection.jsx
│   │   │   ├── TestimonialsSection.jsx
│   │   │   └── CTASection.jsx
│   │   ├── Upload/
│   │   │   ├── PhotoDropzone.jsx
│   │   │   └── ImagePreview.jsx
│   │   ├── Staging/
│   │   │   ├── RoomTypeSelector.jsx
│   │   │   ├── StylePresets.jsx
│   │   │   └── RenderingProgress.jsx
│   │   ├── Results/
│   │   │   ├── BeforeAfterSlider.jsx
│   │   │   ├── MetadataPanel.jsx
│   │   │   └── DownloadButton.jsx
│   │   ├── Dashboard/
│   │   │   └── TimelineView.jsx
│   │   └── Common/
│   │       ├── Header.jsx
│   │       ├── Footer.jsx
│   │       └── LoadingSpinner.jsx
│   ├── pages/
│   │   ├── LandingPage.jsx
│   │   ├── Home.jsx
│   │   ├── Dashboard.jsx
│   │   └── Gallery.jsx
│   ├── hooks/
│   │   ├── useUpload.js
│   │   └── useJobStatus.js
│   ├── services/
│   │   └── api.js
│   └── styles/
│       └── photography-theme.css
```

#### Backend (FastAPI)
```
backend/
├── app/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── images.py
│   │   │   ├── jobs.py
│   │   │   └── users.py
│   │   └── deps.py
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   └── logging.py
│   ├── models/
│   │   ├── image.py
│   │   ├── job.py
│   │   └── user.py
│   ├── schemas/
│   │   ├── image.py
│   │   ├── job.py
│   │   └── user.py
│   ├── services/
│   │   ├── generation.py
│   │   ├── storage.py
│   │   └── worker.py
│   └── main.py
```

#### Worker Layer
- **Queue System**: Redis Queue (RQ)
- **AI Service**: OpenRouter API (always cloud-based, even for local development)
- **Retry Logic**: Exponential backoff, max 3 retries
- **Timeout**: 5 minutes per job

#### Storage
- **Object Storage**: MinIO (S3-compatible, runs locally in Docker)
- **Database**: PostgreSQL with async driver (asyncpg)
- **Cache**: Redis for job status and rate limiting

## 5. Photography-Style UI Design System

### Design Philosophy

The UI design draws inspiration from professional photography software (Adobe Lightroom, Capture One, Luminar) and premium camera interfaces. This approach resonates with real estate photographers and agents who:

- Understand image quality and professional presentation
- Appreciate workflow efficiency and familiar tools
- Value precision controls and metadata awareness
- Expect premium, clean aesthetics

### Color Palette

```css
:root {
  /* Dark theme base - professional photo software aesthetic */
  --bg-primary: #1a1a1a;        /* Main background */
  --bg-secondary: #242424;      /* Panels and cards */
  --bg-tertiary: #2d2d2d;       /* Hover states and borders */
  
  /* Accent colors */
  --accent-primary: #3b82f6;    /* Primary actions - blue */
  --accent-success: #10b981;    /* Success states - green */
  --accent-warning: #f59e0b;    /* In-progress - amber */
  --accent-error: #ef4444;      /* Error states - red */
  
  /* Text colors */
  --text-primary: #f5f5f5;      /* Primary text */
  --text-secondary: #a3a3a3;    /* Secondary text */
  --text-muted: #737373;        /* Muted text */
  
  /* UI elements */
  --border-color: #404040;      /* Borders and dividers */
  --shadow-color: rgba(0, 0, 0, 0.3); /* Drop shadows */
}
```

### Typography

```css
font-family: 
  - Inter,           /* Primary UI text */
  - system-ui,       /* System fallback */
  - -apple-system,   /* Apple system */
  sans-serif;        /* Generic sans-serif */

font-family: 
  - JetBrains Mono,  /* Technical data */
  - Fira Code,
  - SF Mono,
  - Consolas,
  monospace;
```

### Typography Scale

| Element | Size | Weight | Line Height |
|---------|------|--------|-------------|
| Headings | 24-32px | 600 | 1.2 |
| Body text | 14-16px | 400 | 1.5 |
| Metadata | 12px | 500 | 1.4 |
| Labels | 11px | 600 | 1.3 |
| Monospace data | 13px | 400 | 1.5 |

### Before/After Comparison Slider

The signature photography feature - a smooth drag-to-compare interface:

```jsx
// BeforeAfterSlider.jsx
interface BeforeAfterSliderProps {
  originalImage: string;
  stagedImage: string;
  originalAlt?: string;
  stagedAlt?: string;
  initialPosition?: number;
  onSliderChange?: (position: number) => void;
}

function BeforeAfterSlider({
  originalImage,
  stagedImage,
  originalAlt = "Original room photo",
  stagedAlt = "Virtually staged room",
  initialPosition = 50,
  onSliderChange
}: BeforeAfterSliderProps) {
  // Implementation with smooth drag interaction
  // Clipped overlay approach for performance
}
```

### Metadata Panel

EXIF-style display showing image and staging information:

```jsx
// MetadataPanel.jsx
interface MetadataPanelProps {
  image: {
    filename: string;
    width: number;
    height: number;
    fileSize: number;
    format: string;
  };
  staging: {
    roomType: string;
    stylePreset: string;
    generationTime: number;
  };
  technical: {
    jobId: string;
    modelVersion: string;
    confidenceScore: number;
  };
}
```

### Rendering Progress Indicator

Styled like photo rendering/exporting dialogs:

```jsx
// RenderingProgress.jsx
interface RenderingProgressProps {
  jobId: string;
  status: 'queued' | 'processing' | 'complete' | 'error';
  progress: number;
  currentStep: string;
  timeElapsed: number;
  estimatedTimeRemaining: number;
  onCancel?: () => void;
}
```

**Progress Steps:**
| Step | Status Message | Duration |
|------|----------------|----------|
| 1 | Analyzing room layout... | 10-15s |
| 2 | Detecting surfaces and depth... | 15-20s |
| 3 | Generating furniture placement... | 30-60s |
| 4 | Applying style and textures... | 20-30s |
| 5 | Refining lighting and shadows... | 15-20s |
| 6 | Final rendering... | 10-15s |

### Timeline View

Job history displayed as a photography workflow timeline:

```jsx
// TimelineView.jsx
interface TimelineJob {
  id: string;
  thumbnail: string;
  roomType: string;
  stylePreset: string;
  status: 'complete' | 'processing' | 'queued' | 'error';
  createdAt: Date;
  completedAt?: Date;
}
```

## 6. Critical API Endpoints

### 6.1 Image Upload
```http
POST /api/v1/images/upload
Content-Type: multipart/form-data
Authorization: Bearer <token>

Response:
{
  "image_id": "img_abc123",
  "original_url": "http://localhost:9000/stage-uploads/img_abc123.jpg",
  "upload_timestamp": "2026-01-10T10:30:00Z"
}
```

### 6.2 Create Staging Job
```http
POST /api/v1/jobs
Authorization: Bearer <token>

{
  "image_id": "img_abc123",
  "room_type": "living_room",
  "style_presets": ["modern", "minimalist", "traditional"]
}

Response:
{
  "job_id": "job_xyz789",
  "status": "queued",
  "estimated_time_seconds": 180,
  "status_url": "/api/v1/jobs/job_xyz789/status"
}
```

### 6.3 Job Status (Polling)
```http
GET /api/v1/jobs/{job_id}/status
Authorization: Bearer <token>

Response:
{
  "job_id": "job_xyz789",
  "status": "in_progress",
  "progress_percent": 45,
  "status_message": "Generating furniture placement..."
}
```

### 6.4 Job Status (WebSocket)
```
ws://localhost:8000/ws/jobs/{job_id}/updates
```
Stream real-time status updates during generation.

### 6.5 Download Staged Image
```http
GET /api/v1/jobs/{job_id}/download
Authorization: Bearer <token>

Response: Binary image file with embedded disclosure label
Content-Disposition: attachment; filename="staged_living_room_modern.jpg"
```

### 6.6 List User Jobs
```http
GET /api/v1/jobs?limit=20&offset=0
Authorization: Bearer <token>

Response:
{
  "jobs": [
    {
      "job_id": "job_abc123",
      "room_type": "bedroom",
      "style": "cozy",
      "status": "completed",
      "created_at": "2026-01-10T10:30:00Z",
      "thumbnail_url": "http://localhost:9000/stage-thumbnails/job_abc123.jpg"
    }
  ],
  "total": 45,
  "limit": 20,
  "offset": 0
}
```

## 7. Database Schema

```mermaid
erDiagram
    USER ||--o{ JOB : creates
    USER {
        uuid id PK
        string email
        string hashed_password
        int credits_remaining
        timestamp created_at
        timestamp last_login
    }
    
    JOB ||--o{ IMAGE : produces
    JOB {
        uuid id PK
        uuid user_id FK
        uuid image_id FK
        string room_type
        string style_preset
        string status
        int retry_count
        string error_message
        float progress_percent
        string current_step
        int generation_time_seconds
        timestamp created_at
        timestamp started_at
        timestamp completed_at
    }
    
    IMAGE {
        uuid id PK
        uuid user_id FK
        string original_filename
        string original_url
        string room_type
        int width
        int height
        int file_size
        string format
        timestamp created_at
    }
    
    STYLE_PRESET {
        uuid id PK
        string name
        string description
        string thumbnail_url
        boolean is_active
    }
```

## 8. UI Mockups & Wireframes

![UI Mockup](./Gemini_Generated_UI_mockup.png)

### 8.1 Homepage / Upload View (Photography Theme)
```
┌─────────────────────────────────────────────────────────────────┐
│  📷 StageMasterAI                        [My Gallery] [Profile] │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  📁 Import Room Photo                                  │    │
│  │                                                         │    │
│  │  ┌─────────────────────────────────────────────────┐  │    │
│  │  │                                                 │  │    │
│  │  │           ┌─────────────────────────┐           │  │    │
│  │  │           │                         │           │  │    │
│  │  │           │    Drop Zone Area       │           │  │    │
│  │  │           │                         │           │  │    │
│  │  │           │    📸 Drag & drop       │           │  │    │
│  │  │           │    or click to browse   │           │  │    │
│  │  │           │                         │           │  │    │
│  │  │           └─────────────────────────┘           │  │    │
│  │  │                                                 │  │    │
│  │  │  Supported: JPG, PNG • Max 25MB • RAW support   │  │    │
│  │  └─────────────────────────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  📐 Room Type                                           │    │
│  │  ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐                   │    │
│  │  │ 🛋️ │ │ 🛏️  │ │ 🍳  │ │ 🍽️  │ │ 🖥️  │                   │    │
│  │  │ Liv-│ │ Bed-│ │ Kit-│ │ Din-│ │ Off-│                   │    │
│  │  │ ing │ │room │ │ chen│ │ ing │ │ ice │                   │    │
│  │  └────┘ └────┘ └────┘ └────┘ └────┘                   │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  🎨 Style Presets                                       │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐    │    │
│  │  │  MODERN  │ │MINIMALIST│ │TRADITION.│ │   SCANDI │    │    │
│  │  │  ✓       │ │   ✓      │ │   ✓      │ │   ✓      │    │    │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘    │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  [🚀 Render Staging - 1 Credit]                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 8.2 Generation Progress View (Photography Theme)
```
┌─────────────────────────────────────────────────────────────────┐
│  📷 StageMasterAI                        [My Gallery] [Profile] │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  🖼️  Living Room - Modern Style                        │    │
│  │                                                         │    │
│  │  ┌─────────────────────────────────────────────────┐  │    │
│  │  │                                                 │  │    │
│  │  │         ⏳ Rendering...                         │  │    │
│  │  │                                                 │  │    │
│  │  │        ┌────────────────────────────────┐       │  │    │
│  │  │        │                                │       │  │    │
│  │  │        │     ██████████████░░░░░░░░░    │       │  │    │
│  │  │        │        65% Complete             │       │  │    │
│  │  │        │                                │       │  │    │
│  │  │        └────────────────────────────────┘       │  │    │
│  │  │                                                 │  │    │
│  │  │        Applying style and textures...          │  │    │
│  │  │        Elapsed: 1:23  •  Remaining: 0:42       │  │    │
│  │  │                                                 │  │    │
│  │  └─────────────────────────────────────────────────┘  │    │
│  │                                                         │    │
│  │  [✕ Cancel Render]                                     │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 8.3 Results & Download View (Photography Theme)
```
┌─────────────────────────────────────────────────────────────────┐
│  📷 StageMasterAI                        [My Gallery] [Profile] │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────┐  ┌─────────────────────────┐   │
│  │  📸 Before / After          │  │  📊 Metadata           │   │
│  │                             │  │                         │   │
│  │  ┌───────────────────────┐  │  │  Image Info            │   │
│  │  │                       │  │  │  • 4000×3000px        │   │
│  │  │                       │  │  │  • 4.2 MB             │   │
│  │  │   [SLIDER COMPONENT]  │  │  │  • JPEG               │   │
│  │  │                       │  │  │                         │   │
│  │  │                       │  │  │  Staging Details       │   │
│  │  │                       │  │  │  • Living Room        │   │
│  │  │                       │  │  │  • Modern Style       │   │
│  │  │                       │  │  │  • 2.3s render        │   │
│  │  └───────────────────────┘  │  │                         │   │
│  │                             │  │  Technical              │   │
│  │  ← → Drag to compare        │  │  • Job: #abc123        │   │
│  └─────────────────────────────┘  │  • Model: v2.1         │   │
│                                    │  • Confidence: 94%     │   │
│                                    └─────────────────────────┘   │
│                                                                 │
│  ⚠️  Virtual staging disclosure: "This image has been virtually │
│      staged for visualization purposes only."                   │
│                                                                 │
│  [⬇️ Export HD Image]  [🔄 Re-render]  [📤 Share]              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 8.4 Dashboard View (Photography Theme)
```
┌─────────────────────────────────────────────────────────────────┐
│  📷 StageMasterAI                        [My Gallery] [Profile] │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  👋 Welcome back, Agent Smith!                             ▶   │
│                                                                 │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                │
│  │  💳 15      │ │  ⏳ 2        │ │  ✅ 128     │                │
│  │  Credits    │ │  Rendering  │ │  Completed  │                │
│  └─────────────┘ └─────────────┘ └─────────────┘                │
│                                                                 │
│  📁 Recent Projects                                            │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  🖼️  Master Bedroom - Modern  │  ✅ Complete  │ 2h ago │    │
│  ├─────────────────────────────────────────────────────────┤    │
│  │  🖼️  Kitchen - Scandinavian   │  ⏳ Rendering │ 5m ago │    │
│  ├─────────────────────────────────────────────────────────┤    │
│  │  🖼️  Living Room - Minimalist │  ✅ Complete  │ 1d ago │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  [+ New Staging Project]                                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 8.5 Landing Page / Marketing View (Photography Theme)
```
┌─────────────────────────────────────────────────────────────────┐
│  📷 StageMasterAI                       [Sign In] [Start Free]  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    HERO SECTION                          │    │
│  │                                                         │    │
│  │  ┌─────────────────────────────────────────────────┐    │    │
│  │  │                                                 │    │    │
│  │  │         ✨ Transform Empty Rooms into           │    │    │
│  │  │            Stunning Staged Spaces               │    │    │
│  │  │                                                 │    │    │
│  │  │    AI-powered virtual staging for real estate   │    │    │
│  │  │    agents. Get photorealistic results in        │    │    │
│  │  │    minutes, not days.                           │    │    │
│  │  │                                                 │    │    │
│  │  │    ┌─────────────────────────────────────────┐  │    │    │
│  │  │    │  📸 Import Photo → 🎨 Select Style →   │  │    │    │
│  │  │    │         ⏱️ Minutes Later: Export       │  │    │    │
│  │  │    └─────────────────────────────────────────┘  │    │    │
│  │  │                                                 │    │    │
│  │  │    [🚀 Start Staging Free]  [📽️ Watch Demo]   │    │    │
│  │  │                                                 │    │    │
│  │  └─────────────────────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  📊 SOCIAL PROOF                                        │    │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐       │    │
│  │  │ 2,500+  │ │ 98%     │ │ 4.8/5   │ │ 50K+    │       │    │
│  │  │ Agents  │ │ Success │ │ Rating  │ │ Staged  │       │    │
│  │  │         │ │ Rate    │ │         │ │ Rooms   │       │    │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘       │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  💡 FEATURES                                            │    │
│  │                                                         │    │
│  │  ┌─────────────────┐ ┌─────────────────┐               │    │
│  │  │ ⚡ Fast Results │ │ 🎨 Multiple     │               │    │
│  │  │                 │ │     Styles      │               │    │
│  │  │ Get staged      │ │                 │               │    │
│  │  │ images in 3-5   │ │ Choose from     │               │    │
│  │  │ minutes         │ │ Modern,         │               │    │
│  │  │                 │ │ Traditional,    │               │    │
│  │  │                 │ │ Scandinavian    │               │    │
│  │  │                 │ │ & more          │               │    │
│  │  └─────────────────┘ └─────────────────┘               │    │
│  │                                                         │    │
│  │  ┌─────────────────┐ ┌─────────────────┐               │    │
│  │  │ 📱 Professional │ │ ⚖️ Compliant    │               │    │
│  │  │     Workflow    │ │                 │               │    │
│  │  │                 │ │ Auto-generated  │               │    │
│  │  │ Photography-    │ │ disclosure      │               │    │
│  │  │ inspired UI     │ │ labels for MLS  │               │    │
│  │  │ for agents who  │ │ compliance      │               │    │
│  │  │ know quality    │ │                 │               │    │
│  │  └─────────────────┘ └─────────────────┘               │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  🖼️ BEFORE & AFTER EXAMPLES                             │    │
│  │                                                         │    │
│  │  ┌───────────────────┐  ┌───────────────────┐           │    │
│  │  │  📸 Empty Room   │  │ ✨ Staged Result  │           │    │
│  │  │                   │  │                   │           │    │
│  │  │  ┌─────────────┐ │  │ ┌─────────────┐   │           │    │
│  │  │  │             │ │  │ │             │   │           │    │
│  │  │  │             │ │  │ │  🛋️  Modern │   │           │    │
│  │  │  │             │ │  │ │     Living  │   │           │    │
│  │  │  │             │ │  │ │     Room    │   │           │    │
│  │  │  │             │ │  │ │             │   │           │    │
│  │  │  └─────────────┘ │  │ └─────────────┘   │           │    │
│  │  │                   │  │                   │           │    │
│  │  └───────────────────┘  └───────────────────┘           │    │
│  │                                                         │    │
│  │  [View More Examples →]                                 │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  💰 PRICING                                              │    │
│  │                                                         │    │
│  │  ┌─────────────────┐  ┌─────────────────┐               │    │
│  │  │  🆓 Starter    │  │  💎 Pro         │               │    │
│  │  │                 │  │                 │               │    │
│  │  │  5 credits      │  │  50 credits     │               │    │
│  │  │  /month         │  │  /month         │               │    │
│  │  │                 │  │                 │               │    │
│  │  │  Free forever   │  │  $29/month      │               │    │
│  │  │                 │  │                 │               │    │
│  │  │ [Get Started]   │  │ [Go Pro]        │               │    │
│  │  └─────────────────┘  └─────────────────┘               │    │
│  │                                                         │    │
│  │  📝 Enterprise plans available for teams                │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  💬 TESTIMONIALS                                        │    │
│  │                                                         │    │
│  │  ┌─────────────────────────────────────────────────┐    │    │
│  │  │ "The photography-style interface makes it       │    │    │
│  │  │  intuitive for me as a real estate photographer.│    │    │
│  │  │  The before/after slider is professional grade."│    │    │
│  │  │                                                 │    │    │
│  │  │  — Sarah M., Real Estate Agent, NYC            │    │    │
│  │  └─────────────────────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  📧 CTA SECTION                                         │    │
│  │                                                         │    │
│  │  ┌─────────────────────────────────────────────────┐    │    │
│  │  │                                                 │    │    │
│  │  │         Ready to transform your listings?       │    │    │
│  │  │                                                 │    │    │
│  │  │    ┌─────────────────────────────────────┐     │    │    │
│  │  │    │  email@example.com           [→]   │     │    │    │
│  │  │    └─────────────────────────────────────┘     │    │    │
│  │  │                                                 │    │    │
│  │  │    No credit card required • 5 free credits    │    │    │
│  │  │                                                 │    │    │
│  │  └─────────────────────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  📷 StageMasterAI   [Features] [Pricing] [Examples]     │    │
│  │                                                         │    │
│  │  © 2025 StageMasterAI. All rights reserved.  [Privacy] │    │
│  │                                         [Terms]         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 9. Key Risks & Mitigations

| Risk | Impact | Probability | Mitigation Strategy |
|------|--------|-------------|---------------------|
| AI generation quality below expectations | High | Medium | Implement quality gates, allow retries, use configurable AI endpoints |
| Local compute limitations | Medium | High | Design for cloud AI fallback, optimize for local inference |
| Storage performance with MinIO | Low | Low | Use proper instance sizing, enable caching |
| Generation time too long (>5 min) | Medium | Medium | Optimize pipeline, add caching, offer progress estimates |
| Storage costs escalating | Medium | Low | Lifecycle policies, compression, local storage for dev |
| Image upload failures | Medium | Low | Error handling, resumable uploads, validation |
| Compliance/legal issues | High | Low | Auto-embed disclosure labels, audit trail |

## 10. Technology Decisions

### Local Development Stack
- **Frontend**: React 18 + Vite + Tailwind CSS (Node.js container)
- **Backend**: FastAPI (Python 3.12 container)
- **Database**: PostgreSQL 15 (Docker container)
- **Queue**: Redis 7 (Docker container)
- **Storage**: MinIO (S3-compatible, Docker container)
- **Authentication**: JWT with httpx

### AI Service - OpenRouter

The application **always** uses OpenRouter API for AI inference, regardless of deployment environment (local Docker or production). This ensures consistent quality and simplifies deployment.

**Why OpenRouter:**
- Access to multiple AI models (OpenAI, Anthropic, Stability AI, etc.)
- Unified API surface for virtual staging
- Pay-per-use pricing model
- No local GPU required

**Configuration:**
```bash
# .env.local
OPENROUTER_API_KEY=sk-or-v1-your-openrouter-key
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_DEFAULT_MODEL=stability-ai/stable-diffusion-3-large
```

**Recommended Models for Virtual Staging:**
- `google/gemini-3-pro-image-preview` - Best for room understanding
- `google/gemini-3-pro-image-preview` - Also good for photorealistic results
- `google/gemini-3-flash-preview` - For prompt engineering optimization

## 11. Docker Compose Configuration

### Local Development docker-compose.yml

```yaml
version: '3.8'

services:
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    environment:
      - VITE_API_URL=http://localhost:8000
    depends_on:
      - backend

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.dev
    image: python:3.12-slim
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/stage_db
      - REDIS_URL=redis://redis:6379/0
      - STORAGE_ENDPOINT=minio:9000
      - STORAGE_ACCESS_KEY=minioadmin
      - STORAGE_SECRET_KEY=minioadmin
      - STORAGE_BUCKET_UPLOADS=stage-uploads
      - STORAGE_BUCKET_RESULTS=stage-results
      - STORAGE_BUCKET_THUMBNAILS=stage-thumbnails
      - STORAGE_USE_SSL=false
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
      - OPENROUTER_DEFAULT_MODEL=stability-ai/stable-diffusion-3-large
    depends_on:
      - db
      - redis
      - minio

  worker:
    build:
      context: ./backend
      dockerfile: Dockerfile.worker
    volumes:
      - ./backend:/app
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/stage_db
      - REDIS_URL=redis://redis:6379/0
      - STORAGE_ENDPOINT=minio:9000
      - STORAGE_ACCESS_KEY=minioadmin
      - STORAGE_SECRET_KEY=minioadmin
      - STORAGE_BUCKET_RESULTS=stage-results
      - STORAGE_USE_SSL=false
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
      - OPENROUTER_DEFAULT_MODEL=stability-ai/stable-diffusion-3-large
    depends_on:
      - db
      - redis
      - minio

  minio:
    image: minio/minio:latest
    container_name: minio
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    volumes:
      - minio_data:/data
    command: server /data --console-address ":9001"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 20s
      retries: 3

  db:
    image: postgres:15
    container_name: postgres
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: stage_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  minio_data:
  postgres_data:
  redis_data:
```

### Startup Commands for Local Development

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Stop and remove volumes (fresh start)
docker-compose down -v

# Initialize MinIO buckets
docker-compose exec minio mc mb stage-uploads
docker-compose exec minio mc mb stage-results
docker-compose exec minio mc mb stage-thumbnails

# Run database migrations
docker-compose exec backend alembic upgrade head

# Seed initial data
docker-compose exec backend python -m app.seed_data
```

## 12. TODO List for AI Coding Agent

### Phase 1: Foundation Setup
- [ ] Create project directory structure with backend/ and frontend/ folders
- [ ] Set up Python virtual environment and install FastAPI dependencies
- [ ] Initialize React + Vite + Tailwind frontend project
- [ ] Configure Tailwind with photography theme colors and typography
- [ ] Create docker-compose.yml with services: backend, frontend, postgres, redis, minio
- [ ] Configure environment files (.env.example, .env.local) for all services
- [ ] Implement basic JWT authentication with single-user mode
- [ ] Set up PostgreSQL database with async driver connection
- [ ] Create SQLAlchemy models: User, Image, Job, StylePreset
- [ ] Generate database migrations with Alembic
- [ ] Configure MinIO storage service with bucket setup
- [ ] Set up logging infrastructure with structured JSON logs
- [ ] Create health check endpoints for all services

### Phase 1.5: Photography Design System
- [ ] Create photography theme CSS variables and utilities
- [ ] Build BeforeAfterSlider component with smooth drag interaction
- [ ] Create RenderingProgress component with time estimates
- [ ] Implement MetadataPanel component
- [ ] Build TimelineView component
- [ ] Create Dropzone component with photography terminology
- [ ] Add animation keyframes (shimmer, pulse, fadeIn)

### Phase 1.6: Landing Page Implementation
- [ ] Create LandingPage component with hero section
- [ ] Implement features section with photography-focused messaging
- [ ] Build before/after examples gallery with BeforeAfterSlider
- [ ] Create pricing section with Starter and Pro tiers
- [ ] Implement testimonials carousel component
- [ ] Build email capture CTA section
- [ ] Create Footer component with navigation links
- [ ] Add responsive design for mobile/tablet/desktop
- [ ] Implement smooth scroll navigation
- [ ] Add animation effects for engagement
- [ ] Create LandingPage.jsx that assembles all sections

### Phase 2: Core Upload Flow
- [ ] Implement drag-and-drop image upload component with React Dropzone
- [ ] Add file validation: JPG/PNG only, max 25MB, image type detection
- [ ] Create room type selection UI with icons (Living Room, Bedroom, Kitchen, etc.)
- [ ] Build style preset selection interface with visual thumbnails
- [ ] Implement MinIO storage service with S3 upload functionality
- [ ] Add image metadata storage in PostgreSQL (width, height, fileSize, format)
- [ ] Create upload progress indicator for large files
- [ ] Implement error handling with retry UI for upload failures
- [ ] Add client-side image compression before upload

### Phase 3: Generation Pipeline
- [ ] Set up Redis Queue (RQ) worker infrastructure
- [ ] Create job creation endpoint returning job_id and status
- [ ] Integrate OpenRouter API for AI generation service
- [ ] Build job status tracking with progress percentage and current step
- [ ] Implement WebSocket connection for real-time status updates
- [ ] Add retry logic with exponential backoff (max 3 retries)
- [ ] Configure job timeout handling (5 minutes maximum)
- [ ] Create error recovery for failed jobs with descriptive messages
- [ ] Implement job cancellation functionality
- [ ] Add queue prioritization for authenticated users

### Phase 4: Results & Download
- [ ] Build results view with BeforeAfterSlider component
- [ ] Implement download endpoint with high-resolution image export
- [ ] Add compliance label embedding as text watermark
- [ ] Create MetadataPanel display with EXIF-style information
- [ ] Create gallery view with TimelineView component
- [ ] Implement pagination for job history
- [ ] Add regeneration functionality for failed/unsatisfactory results
- [ ] Create share link generation with short expiration
- [ ] Implement image deletion with cascade to related jobs
- [ ] Add thumbnail generation for gallery view
- [ ] Create image transformation service for resizing/cropping

### Phase 5: Polish & Production Readiness
- [ ] Add comprehensive logging for success/failure rates, timing metrics
- [ ] Implement rate limiting to prevent abuse (requests per minute)
- [ ] Create API documentation with OpenAPI/Swagger
- [ ] Configure CORS settings for frontend-backend communication
- [ ] Set up error boundaries and graceful degradation on frontend
- [ ] Optimize image processing pipeline for performance
- [ ] Add unit tests for core functionality (upload, job creation, status)
- [ ] Implement integration tests for API endpoints
- [ ] Configure nginx reverse proxy for production deployment
- [ ] Set up Prometheus metrics endpoints
- [ ] Create deployment scripts for production

## 13. Future Enhancements (Post-MVP)

### Multi-Photo Consistency
- Maintain consistent furniture/decor across multiple room photos
- Property-level style coherence and visual continuity

### Advanced Editing
- Remove/replace specific furniture items with AI segmentation
- Custom furniture placement with drag-and-drop interface
- Style mixing and customization options
- Object removal for decluttering

### Room Understanding Improvements
- Automatic room type detection from image analysis
- Wall/floor/ceiling segmentation for better editing
- Lighting adjustment (relight) based on room conditions
- Automatic clutter detection and removal

### Photography Features
- Batch processing with multiple room photos
- RAW file support for professional photographers
- Custom style presets with saved configurations
- Export presets (MLS, social media, print)
- Histogram and image analysis tools
- Color temperature and tint adjustments
- Lens correction and perspective adjustment

### Integrations & Enterprise
- Team workflows with role-based access control
- Usage-based billing with credit system
- Audit trails and compliance reporting
- MLS/CRM integrations

### Advanced Compliance
- Customizable watermark options and branding
- MLS-ready export formats with metadata
- Multi-language support for international markets

---

## 14. Local Development Quick Start

### Prerequisites
```bash
# Install Docker Desktop
# https://www.docker.com/products/docker-desktop/

# Install Docker Compose
# Included with Docker Desktop
```

### Setup Steps
```bash
# 1. Clone repository
git clone <repository-url>
cd stage-master

# 2. Copy environment file
cp .env.example .env.local

# 3. Start all services
docker-compose up -d

# 4. Wait for services to be healthy
docker-compose ps

# 5. Initialize database
docker-compose exec backend alembic upgrade head

# 6. Open application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
# MinIO Console: http://localhost:9001
```

### Testing the Application
```bash
# 1. Create a test user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "securepassword"}'

# 2. Upload an image
curl -X POST http://localhost:8000/api/v1/images/upload \
  -H "Authorization: Bearer <token>" \
  -F "file=@/path/to/room.jpg"

# 3. Create a staging job
curl -X POST http://localhost:8000/api/v1/jobs \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"image_id": "<image_id>", "room_type": "living_room", "style_presets": ["modern"]}'

# 4. Check job status
curl http://localhost:8000/api/v1/jobs/<job_id>/status \
  -H "Authorization: Bearer <token>"
```

---

*Plan Version: 5.0*  
*Last Updated: 2026-01-11*  
*Status: Ready for Implementation*
