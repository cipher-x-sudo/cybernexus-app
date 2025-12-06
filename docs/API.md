# CyberNexus API Reference

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

### Login
```http
POST /auth/login
Content-Type: application/x-www-form-urlencoded

username=admin&password=admin123
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### Register
```http
POST /auth/register
Content-Type: application/json

{
  "username": "newuser",
  "email": "user@example.com",
  "password": "password123"
}
```

## Entities

### List Entities
```http
GET /entities?entity_type=domain&severity=high&limit=100
Authorization: Bearer <token>
```

### Create Entity
```http
POST /entities
Authorization: Bearer <token>
Content-Type: application/json

{
  "type": "domain",
  "value": "example.com",
  "severity": "medium",
  "source": "WebRecon",
  "tags": ["subdomain", "active"]
}
```

### Get Entity
```http
GET /entities/{entity_id}
Authorization: Bearer <token>
```

### Update Entity
```http
PUT /entities/{entity_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "severity": "high",
  "tags": ["critical", "investigate"]
}
```

### Delete Entity
```http
DELETE /entities/{entity_id}
Authorization: Bearer <token>
```

## Graph

### Get Full Graph
```http
GET /graph?limit=1000&entity_types=domain,ip
Authorization: Bearer <token>
```

**Response:**
```json
{
  "nodes": [
    {"id": "1", "label": "example.com", "type": "domain", "severity": "medium"}
  ],
  "edges": [
    {"id": "e1", "source": "1", "target": "2", "relation": "resolves_to"}
  ]
}
```

### Get Node Neighbors
```http
GET /graph/node/{node_id}/neighbors?depth=2&direction=both
Authorization: Bearer <token>
```

### Find Path
```http
GET /graph/path?source=1&target=5&algorithm=dijkstra
Authorization: Bearer <token>
```

### Find Clusters
```http
GET /graph/clusters?min_size=3
Authorization: Bearer <token>
```

## Threats

### List Threats
```http
GET /threats?severity=critical&status=active&sort_by=score&limit=50
Authorization: Bearer <token>
```

### Get Top Threats
```http
GET /threats/top?n=10
Authorization: Bearer <token>
```

### Get Threat Stats
```http
GET /threats/stats
Authorization: Bearer <token>
```

**Response:**
```json
{
  "total": 142,
  "active": 89,
  "critical": 8,
  "high": 23,
  "medium": 45,
  "low": 13,
  "by_category": {"misconfiguration": 34, "credential_exposure": 28},
  "avg_score": 62.5
}
```

### Create Threat
```http
POST /threats
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "Exposed S3 Bucket",
  "description": "Publicly accessible bucket",
  "severity": "critical",
  "category": "misconfiguration",
  "source": "WebRecon",
  "score": 95
}
```

## Timeline

### Get Timeline
```http
GET /timeline?event_type=threat_detected&severity=critical&limit=100
Authorization: Bearer <token>
```

### Get Recent Events
```http
GET /timeline/recent?n=20&severity_filter=critical,high
Authorization: Bearer <token>
```

### Get Events in Range
```http
GET /timeline/range?start=2024-01-01T00:00:00&end=2024-01-31T23:59:59&granularity=day
Authorization: Bearer <token>
```

## Reports

### List Templates
```http
GET /reports/templates
Authorization: Bearer <token>
```

### Generate Report
```http
POST /reports/generate
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "Weekly Security Report",
  "type": "executive_summary",
  "format": "pdf",
  "date_range_start": "2024-01-01T00:00:00",
  "date_range_end": "2024-01-07T23:59:59"
}
```

### Download Report
```http
GET /reports/{report_id}/download
Authorization: Bearer <token>
```

## WebSocket

### Connect
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/connect/client-123');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data);
};
```

### Subscribe to Channel
```javascript
ws.send(JSON.stringify({
  action: 'subscribe',
  channel: 'threats'
}));
```

### Message Types
- `connected` - Connection established
- `subscribed` - Subscribed to channel
- `threat` - New threat detected
- `event` - New timeline event
- `alert` - Alert notification
- `scan_progress` - Scan progress update

## Error Responses

```json
{
  "detail": "Error message here"
}
```

**Status Codes:**
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error


