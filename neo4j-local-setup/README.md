# Neo4j Local Setup

Small local project for setting up Salesforce-style schema and sample data in a local Neo4j instance.
The schema and seed dataset are aligned with `salesforce-hybrid-sim` so both projects use the same Accounts, Contacts, Opportunities, Cases, Campaigns, Users, Tasks, and relationship IDs.

## What It Does

- connects to local Neo4j using env-driven config
- creates Salesforce-style constraints and indexes
- loads sample nodes and relationships from JSON using the same section layout as `salesforce-hybrid-sim`
- optionally resets the graph first
- verifies the loaded counts after setup
- exposes a small read-only Salesforce-style mock API on top of Neo4j

## Project Files

- `neo4j_setup/main.py` - CLI entrypoint
- `neo4j_setup/api.py` - FastAPI mock API
- `neo4j_setup/repository.py` - Neo4j-backed read queries
- `neo4j_setup/schema.py` - schema and indexes
- `neo4j_setup/seed.py` - sample data loading and relationship creation
- `data/sample_graph.json` - seed dataset
- `.env.example` - local Neo4j connection template

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and set your local Neo4j password:

```powershell
Copy-Item .env.example .env
```

## Run

Apply schema and load sample data:

```powershell
python -m neo4j_setup.main
```

Reset the database first:

```powershell
python -m neo4j_setup.main --reset
```

Apply schema only:

```powershell
python -m neo4j_setup.main --schema-only
```

Use a different data file:

```powershell
python -m neo4j_setup.main --data-file data\\sample_graph.json
```

## Run The Mock API

Start the seeded graph API:

```powershell
uvicorn neo4j_setup.api:app --reload
```

Example endpoints:

- `GET /healthz`
- `GET /accounts`
- `GET /accounts/{account_id}`
- `GET /accounts/{account_id}/contacts`
- `GET /accounts/{account_id}/opportunities`
- `GET /accounts/{account_id}/cases`
- `GET /opportunities`
- `GET /cases`
- `GET /campaigns`

## Seed Model

The included sample dataset creates:

- `Account`
- `Contact`
- `Opportunity`
- `Case`
- `Campaign`
- `User`
- `Task`

And sample relationships such as:

- `WORKS_FOR`
- `FOR_ACCOUNT`
- `TARGETS`
- `INFLUENCED`
- `OWNS`
- `RELATED_TO`
- `INVOLVES_CONTACT`
- `PARENT_OF`

The sample JSON keeps the same foreign-key style fields as the hybrid SQLite model, for example:

- `contacts[].account_id`
- `opportunities[].account_id`
- `opportunities[].owner_user_id`
- `cases[].account_id`
- `campaigns[].account_id`
- `tasks[].opportunity_id`
- `tasks[].case_id`

## Intended Use

This project is designed to simulate Salesforce-style connected business data in Neo4j for:

- local demos
- Graph RAG experiments
- agent workflows
- account/contact/opportunity/case relationship analysis

Use Neo4j as the relationship graph, and keep Salesforce-like validation or security rules in a separate service layer.
