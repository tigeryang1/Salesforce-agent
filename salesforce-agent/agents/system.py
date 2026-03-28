from __future__ import annotations

import os
from typing import Any

from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.types import Command

from agents.context import AgentContext, WorkflowState
from agents.mcp_client import build_mcp_client, scope_tools_for_agent
from agents.nodes.analysis import make_analysis_node
from agents.nodes.approval import human_approval_node
from agents.nodes.compliance import make_compliance_node
from agents.nodes.context_agent import make_context_node
from agents.nodes.discovery import make_discovery_node
from agents.nodes.execution import make_execution_node
from agents.nodes.supervisor import make_supervisor_node
from agents.prompts import (
    ANALYSIS_PROMPT,
    CONTEXT_PROMPT,
    DISCOVERY_PROMPT,
    EXECUTION_PROMPT,
    SUPERVISOR_PROMPT,
)
from agents.routing import route_after_analysis, route_compliance, route_intent


class SalesforceAgentSystem:
    def __init__(self, graph, agent_context: AgentContext, checkpointer: MemorySaver) -> None:
        self.graph = graph
        self.agent_context = agent_context
        self.checkpointer = checkpointer

    async def run(self, user_input: str, thread_id: str = "default") -> dict[str, Any]:
        return await self.graph.ainvoke(
            {
                "user_input": user_input,
                "agent_context": self.agent_context,
                "phase": "route",
            },
            config={"configurable": {"thread_id": thread_id}},
        )

    async def resume_approval(
        self,
        decision: str,
        approval_token: str,
        thread_id: str = "default",
    ) -> dict[str, Any]:
        return await self.graph.ainvoke(
            Command(resume={"decision": decision, "approval_token": approval_token}),
            config={"configurable": {"thread_id": thread_id}},
        )


async def build_agent_system(
    *,
    session_token: str,
    mcp_url: str,
    model: str,
    agent_context: AgentContext,
    checkpointer: MemorySaver | None = None,
) -> SalesforceAgentSystem:
    client = await build_mcp_client(session_token=session_token, mcp_url=mcp_url)
    all_tools = await client.get_tools()
    llm = build_chat_model(model)

    discovery_tools = [
        tool
        for tool in scope_tools_for_agent(all_tools, "read", agent_context)
        if tool.name in {"search_advertiser", "search_global", "resolve_company_context"}
    ]
    context_tools = [
        tool
        for tool in scope_tools_for_agent(all_tools, "read", agent_context)
        if tool.name in {"get_advertiser_context"}
    ]
    execution_tools = scope_tools_for_agent(all_tools, "execution", agent_context)

    supervisor_agent = create_agent(model=llm, tools=[], system_prompt=SUPERVISOR_PROMPT)
    discovery_agent = create_agent(
        model=llm,
        tools=discovery_tools,
        system_prompt=DISCOVERY_PROMPT,
    )
    context_agent = create_agent(
        model=llm,
        tools=context_tools,
        system_prompt=CONTEXT_PROMPT,
    )
    analysis_agent = create_agent(model=llm, tools=[], system_prompt=ANALYSIS_PROMPT)
    execution_agent = create_agent(
        model=llm,
        tools=execution_tools,
        system_prompt=EXECUTION_PROMPT,
    )

    supervisor_node = make_supervisor_node(supervisor_agent)
    discovery_node = make_discovery_node(discovery_agent)
    context_node = make_context_node(
        client=client,
        context_agent=context_agent,
        context_tools=context_tools,
        agent_context=agent_context,
        session_token=session_token,
    )
    analysis_node = make_analysis_node(analysis_agent)
    compliance_node = make_compliance_node(agent_context)
    execution_node = make_execution_node(execution_agent=execution_agent, session_token=session_token)

    graph = StateGraph(WorkflowState)
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("discovery", discovery_node)
    graph.add_node("context", context_node)
    graph.add_node("analysis", analysis_node)
    graph.add_node("compliance", compliance_node)
    graph.add_node("approval", human_approval_node)
    graph.add_node("execution", execution_node)
    graph.set_entry_point("supervisor")

    graph.add_conditional_edges(
        "supervisor",
        route_intent,
        {"read": "discovery", "write": "discovery", "end": END},
    )
    graph.add_edge("discovery", "context")
    graph.add_edge("context", "analysis")
    graph.add_conditional_edges(
        "analysis",
        route_after_analysis,
        {"read": "supervisor", "write": "compliance", "end": END},
    )
    graph.add_conditional_edges(
        "compliance",
        route_compliance,
        {"approved": "execution", "needs_human": "approval", "blocked": END},
    )
    graph.add_edge("approval", "execution")
    graph.add_edge("execution", "supervisor")

    graph_checkpointer = checkpointer or MemorySaver()
    compiled = graph.compile(checkpointer=graph_checkpointer, interrupt_before=["approval"])
    return SalesforceAgentSystem(compiled, agent_context, graph_checkpointer)


def build_chat_model(model_name: str):
    if model_name.startswith("gemini:"):
        resolved_name = model_name.split(":", 1)[1]
        api_key = os.getenv("GEMINI_API_KEY")
        return ChatGoogleGenerativeAI(
            model=resolved_name,
            google_api_key=api_key,
            temperature=0,
        )

    resolved_name = model_name.split(":", 1)[1] if model_name.startswith("openai:") else model_name
    api_key = os.getenv("OPENAI_API_KEY")
    return ChatOpenAI(model=resolved_name, api_key=api_key, temperature=0)
