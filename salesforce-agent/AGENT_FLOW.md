# Agent Flow

This document captures the implemented workflow in [`C:\Users\tiger\project\salesforce-agent`](C:\Users\tiger\project\salesforce-agent).

## End-to-End Flow

```mermaid
flowchart TD
    A["User / React UI"] --> B["FastAPI Backend<br/>/run or /resume-approval"]
    B --> C["AgentSystemRegistry<br/>load or create workflow"]
    C --> D["LangGraph StateGraph"]

    D --> E["Supervisor Node"]
    E -->|read intent| F["Discovery Node"]
    E -->|write intent| F
    E -->|phase done / error| Z["Final Response"]

    F --> G["Discovery Agent<br/>search_advertiser / search_global"]
    G --> H["Resolved entity_id + confidence"]

    H --> I["Context Node"]
    I --> J["MCP Resources<br/>summary / campaigns / opportunities"]
    J --> K["Context Agent Summary"]

    K --> L["Analysis Node"]
    L --> M["Analysis Agent<br/>recommendations + optional proposed_action"]

    M -->|read path| E
    M -->|write path| N["Compliance Node"]

    N -->|blocked| Z
    N -->|approved| P["Execution Node"]
    N -->|needs human| O["Approval Interrupt"]

    O --> Q["Human Reviewer"]
    Q -->|approve + approval_token| R["/resume-approval"]
    R --> C

    P --> S["Execution Agent<br/>approved write tool call"]
    S --> T["Salesforce MCP Server"]
    T --> U["Write Result"]
    U --> E

    Z --> V["API Response"]
```

## Component View

```mermaid
flowchart LR
    UI["UI / Client"] --> API["FastAPI API"]
    API --> REG["Registry + SQLite Persistence"]
    REG --> GRAPH["LangGraph Workflow"]

    GRAPH --> SUP["Supervisor"]
    GRAPH --> DIS["Discovery"]
    GRAPH --> CTX["Context"]
    GRAPH --> ANL["Analysis"]
    GRAPH --> CMP["Compliance"]
    GRAPH --> APR["Approval Interrupt"]
    GRAPH --> EXE["Execution"]

    DIS --> MCP["Salesforce MCP Server"]
    CTX --> MCP
    EXE --> MCP

    GRAPH --> LLM["ChatOpenAI"]
    SUP --> LLM
    DIS --> LLM
    CTX --> LLM
    ANL --> LLM
    EXE --> LLM
```

## Implemented Node Order

1. `supervisor`
2. `discovery`
3. `context`
4. `analysis`
5. `compliance` on write path
6. `approval` for high-risk writes
7. `execution`
8. back to `supervisor` for final response

## Routing Rules

- `supervisor`
  - `read` -> `discovery`
  - `write` -> `discovery`
  - terminal phase -> end
- `analysis`
  - error -> end
  - read intent -> `supervisor`
  - write intent -> `compliance`
- `compliance`
  - blocked -> end
  - approved -> `execution`
  - needs human -> `approval`

## Main Files

- [`C:\Users\tiger\project\salesforce-agent\agents\system.py`](C:\Users\tiger\project\salesforce-agent\agents\system.py)
- [`C:\Users\tiger\project\salesforce-agent\agents\routing.py`](C:\Users\tiger\project\salesforce-agent\agents\routing.py)
- [`C:\Users\tiger\project\salesforce-agent\agents\nodes\supervisor.py`](C:\Users\tiger\project\salesforce-agent\agents\nodes\supervisor.py)
- [`C:\Users\tiger\project\salesforce-agent\agents\nodes\discovery.py`](C:\Users\tiger\project\salesforce-agent\agents\nodes\discovery.py)
- [`C:\Users\tiger\project\salesforce-agent\agents\nodes\context_agent.py`](C:\Users\tiger\project\salesforce-agent\agents\nodes\context_agent.py)
- [`C:\Users\tiger\project\salesforce-agent\agents\nodes\analysis.py`](C:\Users\tiger\project\salesforce-agent\agents\nodes\analysis.py)
- [`C:\Users\tiger\project\salesforce-agent\agents\nodes\compliance.py`](C:\Users\tiger\project\salesforce-agent\agents\nodes\compliance.py)
- [`C:\Users\tiger\project\salesforce-agent\agents\nodes\approval.py`](C:\Users\tiger\project\salesforce-agent\agents\nodes\approval.py)
- [`C:\Users\tiger\project\salesforce-agent\agents\nodes\execution.py`](C:\Users\tiger\project\salesforce-agent\agents\nodes\execution.py)
