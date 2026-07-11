# ADR-001: Clean Repository and Selective Salvage

**Status:** Accepted  
**Date:** 2026-07-11

## Context

The legacy Homefront repository was designed as a commercial multi-tenant SaaS system with a control plane, tenant cells, support access, commercial entitlement concepts, and a routine-centric frontend. Kinward is a private, single-household Docker-deployed assistant environment.

The product is not in active household use, and no compatibility timeline requires incremental migration.

## Decision

Kinward will be built in a clean repository. The legacy Homefront repository remains an archive and source for selective salvage.

No subsystem moves without an explicit salvage decision. The frontend and database migration history are rebuilt rather than migrated wholesale.

The first client is a responsive web application/PWA. Native Android work is deferred until a proven capability requires it.

## Consequences

- Legacy assumptions cannot silently remain in the active project.
- Useful backend capabilities require deliberate extraction.
- The product documents and vocabulary remain coherent.
- Git history for legacy implementation stays in the archived repository.
- Initial effort favors architecture and salvage validation over feature delivery.
