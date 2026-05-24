# Product Requirements Document: URL Shortener Service

## 1. Overview

A lightweight URL shortener service designed to test the multi-profile orchestration workflow. The service accepts long URLs, generates short codes, redirects users, and tracks basic analytics.

## 2. Feature Description

### Core Features
- **URL Shortening**: Accept a long URL and return a unique short code
- **URL Redirection**: Redirect short code requests to the original long URL
- **Click Tracking**: Track and store the number of times each short URL is accessed
- **Health Check**: Expose a health check endpoint for monitoring

### Out of Scope
- User authentication / accounts
- Custom short codes / aliases
- Expiration dates on URLs
- Rate limiting
- Advanced analytics (geolocation, referrer tracking, device info)
- Admin dashboard
- QR code generation

## 3. User Stories

| ID | Story | Priority |
|---|---|---|
| US-1 | As a user, I want to submit a long URL and receive a short code so that I can share it easily. | Must Have |
| US-2 | As a user, I want to visit a short code and be redirected to the original URL. | Must Have |
| US-3 | As an operator, I want to check the health of the service so that I know it's running. | Must Have |
| US-4 | As a user, I want to see how many times a short URL has been clicked. | Should Have |

## 4. Technical Scope

### In Scope
- REST API with JSON request/response
- In-memory or lightweight persistent storage for URL mappings
- Short code generation (6-character alphanumeric)
- Click count tracking
- Health check endpoint

### Out of Scope
- Database migrations / complex schema
- Caching layer (Redis)
- Background jobs / queues
- Multi-region deployment
- CDN integration
- Authentication / authorization

## 5. Acceptance Criteria

### AC-1: Create Short URL
```
Given a valid long URL
When I POST to /api/shorten with { "url": "https://example.com/very/long/path" }
Then I receive a 201 response with { "shortCode": "abc123", "shortUrl": "https://<host>/abc123", "originalUrl": "https://example.com/very/long/path" }
```

### AC-2: Redirect Short URL
```
Given a short code that exists
When I GET /<shortCode>
Then I receive a 302 redirect to the original URL
And the click count for that code is incremented by 1
```

### AC-3: Redirect Not Found
```
Given a short code that does not exist
When I GET /<shortCode>
Then I receive a 404 response with { "error": "Short code not found" }
```

### AC-4: Get Click Count
```
Given a short code that exists
When I GET /api/stats/<shortCode>
Then I receive a 200 response with { "shortCode": "abc123", "clickCount": 42, "originalUrl": "https://example.com/very/long/path" }
```

### AC-5: Health Check
```
Given the service is running
When I GET /health
Then I receive a 200 response with { "status": "ok", "timestamp": "2024-01-01T00:00:00Z" }
```

### AC-6: Invalid URL
```
Given an invalid or missing URL
When I POST to /api/shorten
Then I receive a 400 response with { "error": "Invalid URL provided" }
```

## 6. API Contract

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/shorten | Create a short URL |
| GET | /:shortCode | Redirect to original URL |
| GET | /api/stats/:shortCode | Get click count for a short code |
| GET | /health | Service health check |

### Request / Response Shapes

#### POST /api/shorten
**Request:**
```json
{
  "url": "string (required, valid URL)"
}
```

**Response 201:**
```json
{
  "shortCode": "string",
  "shortUrl": "string",
  "originalUrl": "string"
}
```

**Response 400:**
```json
{
  "error": "Invalid URL provided"
}
```

#### GET /:shortCode
**Response 302:** Redirect to original URL

**Response 404:**
```json
{
  "error": "Short code not found"
}
```

#### GET /api/stats/:shortCode
**Response 200:**
```json
{
  "shortCode": "string",
  "clickCount": 0,
  "originalUrl": "string"
}
```

**Response 404:**
```json
{
  "error": "Short code not found"
}
```

#### GET /health
**Response 200:**
```json
{
  "status": "ok",
  "timestamp": "string (ISO 8601)"
}
```

## 7. Non-Functional Requirements

| Requirement | Target |
|-------------|--------|
| Response Time (p95) | < 100ms for all endpoints |
| Availability | 99.9% (best effort for test env) |
| Short Code Length | 6 characters, alphanumeric (a-z, A-Z, 0-9) |
| Code Uniqueness | Collision-resistant generation |
| Data Persistence | In-memory acceptable; file/DB optional |
| Port | 8080 (configurable via PORT env var) |

## 8. Data Model

```
URLMapping:
  - shortCode: string (PK)
  - originalUrl: string
  - clickCount: integer (default 0)
  - createdAt: timestamp
```

## 9. Deployment Notes

- Containerized with Docker
- Single binary / process
- Stateless (storage can be in-memory for test purposes)
- Environment variable: `PORT` (default 8080)

---

*Document Version: 1.0*
*Purpose: Multi-profile orchestration workflow test project*
