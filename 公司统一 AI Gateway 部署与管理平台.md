# Role

You are a senior DevOps / platform engineer responsible for deploying a production-ready internal AI Gateway for a 5–10 person biotechnology company.

Your job is to **design, deploy, test, document, and hand off** a lightweight but auditable company AI infrastructure.

Do not over-engineer this project. The target company is small, technically capable, and wants a solution that can be deployed within hours rather than a large enterprise IT project.

---

# 1. Project Goal

Build a company-wide AI Gateway that allows employees to access approved LLM APIs through a single controlled endpoint.

The system must provide:

- Employee-specific identity
- Individual Virtual API Keys
- Per-employee usage tracking
- Token usage tracking
- Cost tracking
- Monthly budget limits
- Daily limits where needed
- Model access control
- Model routing
- Central API provider key management
- Admin dashboard
- Usage auditing
- Employee offboarding / instant key revocation
- Chat interface
- OpenAI-compatible API endpoint for Codex, OpenCode and other agents
- Easy migration from the initial US server to a future China server

The company must be able to answer:

> How much did MED001 spend this month?

> How many tokens did MED002 use?

> Which models did MED003 call?

> Which employee or Agent consumed the most money?

> How much did the entire Medical Department spend?

> How much did each upstream API provider actually charge?

---

# 2. Deployment Strategy

## Phase 1 — Initial deployment

Deploy the complete system on the company's existing **US Linux server**.

The US server is only the initial deployment environment for rapid validation.

Do not make the architecture dependent on the US server.

Everything must be containerized and portable.

---

## Phase 2 — Future migration

Once the workflow is validated, the same stack will later be migrated to a server located in China.

The migration must be simple:

1. Export configuration
2. Backup PostgreSQL
3. Move persistent Docker volumes
4. Deploy the same Docker Compose stack
5. Restore PostgreSQL
6. Change DNS
7. Employees continue using the same domain and credentials

Design everything with this future migration in mind.

---

# 3. Core Architecture

Use this architecture:

```text
Employees
    │
    ├── Web browser
    ├── Open WebUI
    ├── Codex
    ├── OpenCode
    ├── Agent tools
    └── Internal applications
            │
            ▼
    Company AI Gateway
            │
            ▼
         LiteLLM
            │
     ┌──────┼────────┐
     ▼      ▼        ▼
 DeepSeek  Qwen     MiMo
  API      API       API
```

Optional premium models may be added later.

The default production API layer should NOT depend on OpenAI API or Anthropic API.

---

# 4. Model Strategy

The company Gateway should primarily use low-cost APIs:

### Default

- DeepSeek
- Qwen
- MiMo

These models handle:

- Routine chat
- Translation
- Summarization
- Document processing
- PPT generation
- Tool calling
- Agent execution
- File operations
- Structured extraction
- Draft generation

---

## High-quality commercial models

Employees who genuinely need:

- ChatGPT
- Claude

will normally use their own approved paid subscriptions.

These subscriptions may be reimbursed by the company according to internal policy.

Do NOT architect the company Gateway around expensive OpenAI or Anthropic API usage.

OpenAI/Anthropic APIs may later be configured only as optional premium/fallback routes.

---

# 5. Required Components

Use:

### LiteLLM

Purpose:

- Central API Gateway
- Virtual Keys
- Model routing
- User/team tracking
- Spend tracking
- Token tracking
- Budget limits
- Rate limiting
- Provider abstraction
- OpenAI-compatible endpoint

---

### PostgreSQL

Purpose:

Store:

- users
- virtual keys
- usage
- budgets
- spend
- models
- teams
- audit-related metadata

PostgreSQL must use persistent storage.

---

### Open WebUI

Purpose:

Provide a browser-based employee AI interface.

Employees should not need to interact directly with LiteLLM administration.

---

### Optional Redis

Do NOT install Redis unless it provides a concrete benefit at the current scale.

For 5–10 employees, avoid unnecessary infrastructure.

If LiteLLM runs correctly without Redis, omit it initially.

Document how Redis can be added later.

---

# 6. Employee Identity Model

Every employee must have a permanent company AI Employee ID.

Example:

```text
MED001
MED002
MED003

CMC001
CMC002

CLIN001

BD001

FIN001

ADMIN001
```

Do not use a person's name as the primary accounting identifier.

Maintain a mapping separately:

```text
MED001 | Employee Name | Medical
MED002 | Employee Name | Medical
CMC001 | Employee Name | CMC
```

---

# 7. Virtual Key Architecture

Every employee must receive a separate LiteLLM Virtual Key.

Do NOT share one Virtual Key among employees.

Recommended design:

```text
MED001
├── MED001-CHAT
└── MED001-AGENT

MED002
├── MED002-CHAT
└── MED002-AGENT
```

This is important because chat usage and Agent usage need to be measurable separately.

Example:

```text
MED001-CHAT

Allowed models:
- company-fast
- company-standard

Monthly budget:
$30


MED001-AGENT

Allowed models:
- company-fast
- company-standard
- company-agent

Monthly budget:
$50
```

The admin must be able to revoke either key immediately.

---

# 8. Provider Keys

Real provider API keys must NEVER be distributed to employees.

Examples:

```text
DEEPSEEK_API_KEY
DASHSCOPE_API_KEY
MIMO_API_KEY
```

These must only exist as:

- server environment variables
- Docker secrets
- secure deployment secrets

Never:

- hard-code them
- put them in git
- expose them in the Web UI
- give them to employees

Provide a `.env.example` containing placeholders only.

The real `.env` must be excluded through `.gitignore`.

---

# 9. Model Abstraction

Employees should NOT need to know the underlying provider model name.

Expose internal aliases such as:

```text
company-fast

company-standard

company-pro

company-agent
```

Example routing:

```text
company-fast
→ DeepSeek Flash-class model

company-standard
→ MiMo or Qwen

company-pro
→ best approved high-quality domestic API

company-agent
→ model selected for strong tool calling
```

The company must later be able to change:

```text
company-standard
```

from one provider to another without employees changing their configuration.

---

# 10. LiteLLM Requirements

Configure LiteLLM to support:

- PostgreSQL database
- Admin UI
- Virtual Keys
- User IDs
- Teams/departments
- Spend tracking
- Token tracking
- Model restrictions
- Per-key budget
- Per-user budget
- Rate limits
- Provider routing
- Aliased model names
- OpenAI-compatible `/v1` interface

The admin dashboard should allow management to inspect:

```text
Employee ID

Department

Virtual Key alias

Model

Provider

Request count

Prompt/input tokens

Cached tokens if available

Output tokens

Total tokens

Cost

Date

Daily spend

Monthly spend
```

---

# 11. Department Structure

Create at least these example teams:

```text
Medical

CMC

Clinical

BD

Finance

Admin
```

Make the setup easy to modify.

---

# 12. Budget Controls

Provide sensible defaults but make all values configurable.

Example:

### Normal employee

```text
CHAT:
$20–30/month

AGENT:
$30–50/month
```

### High-use Medical employee

```text
CHAT:
$50/month

AGENT:
$50–100/month
```

### Technical/admin user

```text
$100/month
```

Budgets must not be hard-coded into application code.

Use configuration or LiteLLM administrative controls.

---

# 13. Cost Monitoring

Management must have two levels of cost verification.

## Layer 1 — LiteLLM

Employee-level accounting:

```text
MED001     $23.17
MED002     $41.28
MED003     $16.44
CMC001      $7.20
```

---

## Layer 2 — API provider billing

Company must reconcile:

```text
LiteLLM total calculated spend
≈
DeepSeek invoice
+
Qwen invoice
+
MiMo invoice
```

Create documentation explaining how this monthly reconciliation should work.

---

# 14. Open WebUI

Deploy Open WebUI.

Requirements:

- public registration disabled
- admin creates/approves users
- employee usernames should correspond to company IDs
- users must not see upstream provider keys
- users should only see company-approved models
- admin should be able to disable a user
- persistent storage required

Example usernames:

```text
MED001
MED002
CMC001
```

---

# 15. Identity and Cost Attribution

This requirement is CRITICAL.

Do not build:

```text
Open WebUI
→ one shared LiteLLM key
→ LiteLLM
```

if that causes LiteLLM to lose individual cost attribution.

Implement an architecture that reliably associates every request with the employee's identity or Virtual Key.

Preferred solution for Phase 1:

```text
Employee
     ↓
Open WebUI / Agent
     ↓
Employee-specific LiteLLM Virtual Key
     ↓
LiteLLM
```

If Open WebUI supports a cleaner server-side identity mapping, investigate it.

Choose the simplest reliable solution.

Document the reasoning.

---

# 16. Codex / OpenCode Support

Employees running Agent tools must be able to configure:

```text
OPENAI_BASE_URL=https://gateway.company.com/v1

OPENAI_API_KEY=<employee LiteLLM virtual key>
```

or the equivalent supported configuration.

They must NOT receive the real upstream API key.

Example:

```text
Employee:
MED001

Agent key:
MED001-AGENT
```

All Agent usage must therefore appear under:

```text
MED001-AGENT
```

in LiteLLM.

---

# 17. Public Network Exposure

Do NOT directly expose raw service ports such as:

```text
3000
4000
5432
```

to the public internet.

Use:

```text
HTTPS 443
```

with reverse proxy.

Recommended domains:

```text
ai.company-domain.com
gateway.company-domain.com
```

Architecture:

```text
Internet
   │
   ▼
Reverse Proxy / TLS
   │
   ├── ai.company-domain.com
   │      ↓
   │   Open WebUI
   │
   └── gateway.company-domain.com
          ↓
       LiteLLM
```

PostgreSQL must never be public.

---

# 18. TLS

Configure HTTPS.

Use one of:

- Caddy
- Nginx
- Traefik

Choose the simplest production-ready option.

Prefer automatic Let's Encrypt certificate renewal.

Explain the choice.

---

# 19. Firewall

Create firewall recommendations.

Only expose:

```text
22
80
443
```

Prefer:

```text
22 only from administrator IP/VPN
443 public
```

If possible:

```text
80 only for TLS certificate redirect/challenge
```

Database ports remain internal.

---

# 20. LiteLLM Admin Security

The LiteLLM admin interface should NOT be casually accessible by employees.

Preferred options:

### Option A

Admin UI only available from:

- administrator IP
- VPN
- Tailscale

### Option B

Protect admin route through:

- Cloudflare Access
- reverse proxy authentication

Do not expose the admin dashboard openly.

---

# 21. Logging Policy

The company wants usage and cost auditing, but does NOT want to create a central archive of confidential biomedical information unnecessarily.

Default logging should prioritize:

```text
Employee ID

timestamp

model

provider

token usage

cost

request status

latency
```

Avoid storing full prompt and response contents unless necessary.

If LiteLLM or Open WebUI stores prompt content by default, document:

- what is stored
- where it is stored
- how to disable it
- retention settings

Use minimum necessary retention.

---

# 22. Biotechnology Data Policy

Create a short technical usage policy.

Three data classes:

## Level 1 — Public

Examples:

- publications
- public regulations
- public company information
- publicly available scientific information

Allowed.

---

## Level 2 — Internal company information

Examples:

- normal internal drafts
- non-public presentations
- internal reports

Allowed only through approved company AI systems according to company policy.

---

## Level 3 — Sensitive

Examples:

- PHI
- directly identifiable patient information
- participant identity information
- highly sensitive clinical data
- passwords
- secrets
- API keys
- privileged legal materials where AI use has not been approved

Do not upload by default.

Require:

- de-identification
- authorization
- or separate approved environment

Do not build PHI compliance claims into the system unless they are actually supported contractually and technically.

---

# 23. Backups

Implement documented backup procedures for:

### PostgreSQL

Daily backup.

Example retention:

```text
7 daily
4 weekly
3 monthly
```

### Open WebUI data

Back up persistent volume.

### Configuration

Back up:

```text
docker-compose.yml

LiteLLM config

reverse proxy config

.env.example
```

Never copy real secrets into source control.

---

# 24. Recovery

Write a recovery procedure:

```text
New server
↓
Install Docker
↓
Clone deployment configuration
↓
Restore secrets
↓
Restore PostgreSQL
↓
Restore Open WebUI volume
↓
docker compose up -d
↓
Update DNS
```

Goal:

A technically competent person should be able to restore the environment without the original installer.

---

# 25. Migration to China

Create a separate document:

```text
MIGRATION_TO_CHINA.md
```

It should explain how to migrate from the US server to a China server.

Include:

- PostgreSQL dump
- volume backup
- restore
- provider endpoints
- DNS change
- TLS
- testing
- rollback

The software stack itself should not need redesign.

---

# 26. Docker Requirements

Everything should run through Docker Compose.

Expected structure:

```text
company-ai-gateway/

├── docker-compose.yml
├── .env.example
├── .gitignore
│
├── litellm/
│   └── config.yaml
│
├── proxy/
│   └── Caddyfile
│
├── scripts/
│   ├── backup.sh
│   ├── restore.sh
│   ├── healthcheck.sh
│   ├── create-user.sh
│   └── monthly-report.sh
│
├── docs/
│   ├── ADMIN_GUIDE.md
│   ├── EMPLOYEE_GUIDE.md
│   ├── BACKUP_RESTORE.md
│   ├── MIGRATION_TO_CHINA.md
│   ├── SECURITY.md
│   └── COST_MANAGEMENT.md
│
└── README.md
```

Modify the structure if technically justified.

---

# 27. Docker Compose Services

Expected minimum:

```text
litellm

postgres

open-webui

reverse-proxy
```

Do not add unnecessary services.

Use restart policy:

```text
unless-stopped
```

Use health checks where appropriate.

Use Docker internal networks so PostgreSQL is not publicly exposed.

---

# 28. Version Pinning

Do NOT blindly use `latest` everywhere in the final production version.

During initial testing, current stable images can be used.

After successful deployment:

- identify working versions
- pin image versions
- document upgrade procedure

Avoid unexpected automatic major-version changes.

---

# 29. Monitoring

Do not install a giant observability stack unless needed.

Minimum monitoring:

- container health
- disk usage
- service uptime
- PostgreSQL status
- LiteLLM health endpoint
- API provider errors
- monthly spend

Provide:

```text
scripts/healthcheck.sh
```

that verifies all important services.

---

# 30. Monthly Usage Report

Create:

```text
scripts/monthly-report.sh
```

or an equivalent Python script.

Output should provide:

```text
Company total spend

Spend by department

Spend by employee

Spend by model

Spend by provider

Top 10 users

Top Agent users

Request count

Input tokens

Output tokens
```

CSV output is sufficient for Phase 1.

Example:

```text
reports/2026-08-usage.csv
```

If LiteLLM already provides a reliable endpoint for this information, use that API rather than recreating the accounting logic.

---

# 31. Employee Offboarding

Document a procedure.

When employee MED003 leaves:

1. Disable Open WebUI user
2. Revoke MED003-CHAT
3. Revoke MED003-AGENT
4. Verify no other keys exist
5. Record offboarding date

This must take less than five minutes.

---

# 32. Employee Onboarding

Create a simple onboarding command or script.

Example:

```bash
./scripts/create-user.sh MED004 Medical
```

Desired result:

```text
Create employee record

Create CHAT key

Create AGENT key

Assign default budget

Assign approved models

Print credentials securely
```

If automatic creation through LiteLLM API is reliable, implement it.

If not, provide exact administrative steps.

Do NOT create fragile automation merely for appearance.

---

# 33. Security Tests

Before declaring the deployment complete, test:

### Test 1

Employee cannot see provider API key.

### Test 2

MED001 activity is attributed to MED001.

### Test 3

MED001-AGENT is distinguishable from MED001-CHAT.

### Test 4

MED001 cannot access unauthorized premium model.

### Test 5

Revoked Virtual Key stops working immediately.

### Test 6

Database is not reachable from public internet.

### Test 7

Open WebUI public signup is disabled.

### Test 8

Admin dashboard is protected.

### Test 9

Restarting Docker does not lose usage data.

### Test 10

Backup can be restored successfully.

---

# 34. Cost Tests

Create a small controlled usage test.

For example:

```text
MED001-CHAT
→ company-fast
→ 5 requests

MED001-AGENT
→ company-agent
→ 5 requests

MED002-CHAT
→ company-standard
→ 5 requests
```

Then verify LiteLLM shows distinct costs.

Generate a screenshot or documented evidence from the dashboard/API demonstrating this.

---

# 35. Performance Goal

This system is not performing model inference itself.

Therefore the Gateway should have low overhead.

Target:

- Gateway overhead should be negligible compared with model latency
- normal employee chat should feel responsive
- 5–10 simultaneous company users should not require significant infrastructure

Do not optimize for thousands of concurrent users.

---

# 36. Initial Infrastructure Requirements

Because inference happens upstream, expected server resources are modest.

Start approximately with:

```text
2–4 vCPU

4 GB RAM minimum

8 GB RAM preferred

20–50 GB SSD
```

Measure actual usage.

Do not prematurely provision expensive infrastructure.

---

# 37. Important Cost Philosophy

Do NOT optimize only for the cheapest possible AI usage.

The objective is:

```text
high employee productivity
+
high-quality output
+
central management
+
predictable cost
+
minimum unnecessary fixed subscription cost
```

Do not impose overly restrictive employee limits that reduce productivity.

Budgets exist to:

- detect abuse
- detect runaway Agents
- identify abnormal consumption
- understand real usage

not to discourage legitimate work.

---

# 38. OpenAI / Anthropic API Policy

Do not make OpenAI or Anthropic API the default route.

Reason:

Fixed ChatGPT / Claude subscriptions often provide dramatically more practical interactive usage per dollar than equivalent heavy API workloads.

For:

- long documents
- PPT work
- repeated revisions
- Agent loops
- tool calls

API expenditure can become much larger than subscription cost.

Therefore:

```text
Company Gateway
→ primarily low-cost domestic APIs

High-quality human-interactive work
→ approved ChatGPT / Claude subscriptions

OpenAI / Anthropic API
→ optional premium fallback only
```

---

# 39. Deliverables

At completion I expect:

### Working deployment

Accessible through HTTPS.

---

### Repository

Containing all deployment files.

---

### README

Must explain:

- architecture
- deployment
- startup
- shutdown
- upgrade
- troubleshooting

---

### ADMIN_GUIDE.md

Explain:

- creating employee
- revoking employee
- resetting budget
- assigning model
- reading spend dashboard
- monthly reconciliation

---

### EMPLOYEE_GUIDE.md

One-page simple instructions:

```text
How to login

How to select models

How to use Agent API key

What data cannot be uploaded

Who to contact for problems
```

---

### COST_MANAGEMENT.md

Explain:

- LiteLLM spend
- provider invoices
- monthly reconciliation
- budget management
- abnormal usage investigation

---

### SECURITY.md

Explain:

- key management
- TLS
- firewall
- admin protection
- logging
- backup
- confidential data rules

---

### MIGRATION_TO_CHINA.md

Complete migration procedure.

---

### `.env.example`

No secrets.

---

### `docker-compose.yml`

Production ready.

---

### LiteLLM config

With provider placeholders and model aliases.

---

### Backup and restore scripts

Tested.

---

### Monthly reporting script

Tested.

---

# 40. Execution Method

Do NOT immediately start making random changes.

Follow this sequence.

## Step 1 — Inspect

Inspect:

- current server OS
- Docker availability
- open ports
- firewall
- existing reverse proxy
- domain availability
- directory structure

Do not delete or change unrelated server services.

---

## Step 2 — Plan

Create:

```text
IMPLEMENTATION_PLAN.md
```

Include:

- architecture
- services
- ports
- domains
- security model
- identity model
- provider configuration
- backup design
- migration design

Show me the plan before executing major infrastructure changes.

---

## Step 3 — Implement

After the plan is approved:

- create files
- deploy containers
- configure TLS
- configure LiteLLM
- configure Open WebUI
- configure PostgreSQL
- configure users
- test provider routes

---

## Step 4 — Validate

Run all security, identity, cost, persistence and recovery tests.

Do not call deployment complete merely because the containers are running.

---

## Step 5 — Document

Produce all requested documentation.

---

# 41. Engineering Principles

Follow these principles:

### Simplicity

This is a 5–10 person company.

Do not build Kubernetes.

Do not add unnecessary microservices.

Do not add enterprise complexity without a concrete need.

---

### Portability

The system must move easily from the US server to China.

---

### Auditability

Every paid API call must be attributable to:

```text
employee
or
specific Agent key
```

---

### Security

Provider secrets remain server-side.

---

### Maintainability

A technically capable non-specialist should be able to maintain this environment.

---

### No vendor lock-in

Employees use internal model aliases.

Providers can be switched centrally.

---

# 42. Definition of Done

The project is complete only when all of the following are true:

```text
[ ] Open WebUI accessible over HTTPS

[ ] LiteLLM Gateway accessible over HTTPS

[ ] PostgreSQL persistent and private

[ ] DeepSeek API working

[ ] Qwen API working

[ ] MiMo API working if credentials are available

[ ] Employee-specific Virtual Keys working

[ ] CHAT and AGENT keys separately tracked

[ ] Per-employee cost visible

[ ] Token usage visible

[ ] Per-model usage visible

[ ] Department usage visible or exportable

[ ] Monthly budgets configurable

[ ] Unauthorized model access blocked

[ ] Employee key revocation tested

[ ] Provider keys hidden from employees

[ ] Public signup disabled

[ ] Admin UI protected

[ ] Backup tested

[ ] Restore tested

[ ] Docker restart persistence tested

[ ] Monthly report generated

[ ] Documentation complete

[ ] Migration procedure documented
```

---

# Final instruction

Treat this as a **small-company production deployment**, not a demonstration.

Prioritize:

**simple > complicated**

**auditable > clever**

**portable > server-specific**

**secure > convenient shortcuts**

**working automation > unnecessary architecture**

**employee productivity > artificial usage restrictions**

Before making major changes, first inspect the environment and give me the implementation plan. After I approve the plan, execute the deployment step by step and validate every requirement above.