# Project Alpha — Architecture Decision Record

## Overview
Project Alpha is a microservices-based e-commerce platform. The team has decided
to use **event-driven architecture** with Apache Kafka for inter-service communication.

## Current Tech Stack
- **Backend**: Python (FastAPI) + Go (order processing)
- **Frontend**: React with TypeScript
- **Database**: PostgreSQL for transactional data, Redis for caching
- **Message Broker**: Apache Kafka
- **Deployment**: Kubernetes on GCP (GKE)

## Key Architectural Decisions

### ADR-001: API Gateway Pattern
We use Kong as our API Gateway. All external traffic routes through Kong,
which handles rate limiting, authentication, and request routing.

### ADR-002: Database Per Service
Each microservice owns its data. The User Service uses PostgreSQL,
the Product Catalog uses MongoDB, and the Order Service uses PostgreSQL
with event sourcing.

### ADR-003: Authentication
We use OAuth 2.0 with JWT tokens. The Auth Service issues short-lived
access tokens (15 min) and refresh tokens (7 days). All inter-service
communication uses service accounts with mTLS.

## Sprint Planning Notes
- **Current Sprint (Sprint 14)**: Focus on checkout flow optimization
- **Next Sprint (Sprint 15)**: Payment gateway integration with Stripe
- **Tech Debt**: Need to migrate legacy order validation from monolith

## Team Preferences
- Code reviews require 2 approvals minimum
- All PRs must include unit tests with >80% coverage
- We follow trunk-based development with feature flags
- Deployments happen every Tuesday and Thursday
