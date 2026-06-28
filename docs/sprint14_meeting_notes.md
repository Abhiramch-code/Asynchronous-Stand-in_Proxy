# Meeting Notes — Sprint 14 Kickoff

**Date**: 2026-06-15
**Attendees**: Abhiram, Sarah (PM), Mike (Backend Lead), Lisa (Frontend)

## Action Items from Last Sprint
- [x] Abhiram: Finalize Kafka topic schema for order events
- [x] Mike: Set up staging environment for load testing
- [ ] Lisa: Complete React component library documentation

## Sprint 14 Goals
1. **Checkout Flow Optimization** — Reduce checkout latency from 3s to under 1s
2. **Cart Persistence** — Implement Redis-backed cart that survives session expiry
3. **Error Handling** — Add circuit breaker pattern to payment service calls

## Technical Discussion

### Checkout Latency
Abhiram proposed using **async processing** for inventory checks during checkout.
Instead of synchronous calls to the Inventory Service, we'll publish a Kafka event
and use optimistic locking. If inventory is insufficient, we'll roll back within
the 30-second payment hold window.

### Cart Persistence Strategy
The team agreed to use Redis with a **7-day TTL** for cart data. Cart items will be
serialized as JSON with product snapshots (price at time of add) to handle price
changes gracefully.

### Abhiram's Opinions on Architecture
- Prefers **event sourcing** over CRUD for order management
- Strongly advocates for **infrastructure as code** (Terraform)
- Believes we should adopt **gRPC** for internal service communication by Q3
- Against adding GraphQL — "REST is sufficient for our current scale"

## Budget & Timeline
- Current cloud spend: $12,400/month on GCP
- Projected increase with Kafka: +$2,100/month
- Sprint 15 delivery deadline: July 15, 2026
- Q3 milestone: Full payment integration live by September 30, 2026
