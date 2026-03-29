# Salesforce Hybrid Sim

Hybrid Salesforce simulation project using:

- `SQLite` as the source of truth for Salesforce-style records
- `Neo4j` as the projected relationship graph
- `FastAPI` as the local mock service layer

## What It Does

- creates a local SQLite schema for Accounts, Contacts, Opportunities, Cases, Campaigns, Users, and Tasks
- loads sample Salesforce-style seed data into SQLite
- projects the relational data into Neo4j nodes and relationships
- exposes read APIs from SQLite
- exposes admin endpoints to reseed SQLite and resync the Neo4j graph

## Setup

```powershell
cd C:\Users\tiger\project\salesforce-monorepo\salesforce-hybrid-sim
pip install -r requirements.txt
Copy-Item .env.example .env
```

## Run

```powershell
uvicorn salesforce_hybrid_sim.api:app --reload --port 8010
```

