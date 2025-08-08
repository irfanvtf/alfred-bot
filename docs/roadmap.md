# Alfred Bot Roadmap

## Current Status

- [x] **Phase 1**: Project setup & environment
- [x] **Phase 2**: Data preparation & knowledge base creation
- [x] **Phase 3**: Redis session management
- [x] **Phase 4**: Vector embedding & search with Chroma
- [x] **Phase 5**: Core chatbot logic
- [x] **Phase 6**: FastAPI integration
- [x] **Phase 7**: Performance optimization & deployment (Docker)
- **Current Metrics**: 85% intent accuracy, <200ms response time, >95% session reliability

## High Priority Phase (Current Focus)

### Phase 8: Multi-language Support (Malay + English)

- [ ] Language-specific JSON intent-response structure
- [ ] Separate language files (malay.json, english.json)
- [ ] Language mode selection at conversation start
- [ ] CSV export functionality for Unity integration (key-value translation pairs)
- [ ] Language-aware response routing
- [ ] Validation for bilingual content completeness

### Phase 9: Remote Deployment Solution

- [ ] Remote deployment API/interface
- [ ] Secure authentication for remote operations
- [ ] Docker compose orchestration via web interface
- [ ] Deployment status monitoring & logging
- [ ] Rollback capabilities for failed deployments
- [ ] Configuration management for multiple environments
- [ ] Replace AnyDesk dependency with web-based solution

### Phase 10: Media Server Implementation

- [ ] Static media server setup (images/audio)
- [ ] QR code and banner image storage/serving
- [ ] Pre-generated audio response management
- [ ] Media upload and organization interface
- [ ] CDN-like serving with proper headers
- [ ] Media versioning and cleanup utilities

### Phase 11: CMS Refactoring

- [ ] Evaluate monorepo architecture (Next.js/React vs current setup)
- [ ] User-friendly interface design for non-technical users
- [ ] Simplified content creation workflows
- [ ] WYSIWYG editor for responses
- [ ] Bulk operations (import/export/copy)
- [ ] Content preview and testing features
- [ ] Role-based access (admin/content manager)

### Phase 12: Project Documentation

- [ ] **Technical Documentation**
  - Architecture overview and system design
  - API documentation (OpenAPI/Swagger)
  - Database schema and data flow diagrams
  - Deployment and configuration guides
- [ ] **User Documentation**
  - CMS user manual with screenshots
  - Content management best practices
  - Troubleshooting and FAQ sections
- [ ] **Developer Documentation**
  - Contributing guidelines and code standards
  - Local development setup
  - Testing procedures and guidelines

## Supporting Tasks

### Infrastructure & DevOps

- [ ] Docker optimization for faster builds
- [ ] Environment configuration templates
- [ ] Health check endpoints for all services
- [ ] Backup and restore procedures

### Quality Assurance

- [ ] Automated testing for multi-language flows
- [ ] Media server performance testing
- [ ] CMS usability testing with non-technical users
- [ ] End-to-end deployment validation

### Security & Performance

- [ ] Secure remote access implementation
- [ ] Media server security (file type validation, size limits)
- [ ] Performance monitoring for new components
- [ ] Basic security audit for remote deployment features

## Success Metrics

- [ ] Multi-language support with <5% accuracy drop
- [ ] Remote deployment success rate >95%
- [ ] Media serving <100ms response time
- [ ] CMS usability score >4/5 from non-technical users
- [ ] Complete documentation coverage for all components

## Technical Decisions Pending

- [ ] Monorepo vs separate repositories for CMS
- [ ] React/Next.js vs lightweight alternatives for CMS
- [ ] Media storage strategy (local vs cloud-ready)
- [ ] Remote deployment security model

---

_Current Version: 0.9.0 | Next Target: 1.0.0 | Focus: Multi-language & Remote Deployment_
