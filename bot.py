from langchain_google_vertexai import ChatVertexAI
from langgraph.graph import MessagesState
from langgraph.types import Command
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent

llm = ChatVertexAI(model="gemini-1.5-flash",temperature="0")
members = ["researcher"]
options = members + ["FINISH"]

def make_system_prompt(suffix: str) -> str:
    return (
        "You are a helpful AI assistant, collaborating with other assistants."
        " Use the provided tools to progress towards answering the question."
        " If you are unable to fully answer, that's OK, another assistant with different tools "
        " will help where you left off. Execute what you can to make progress."
        " If you or any of the other assistants have the final answer or deliverable,"
        " prefix your response with FINAL ANSWER so the team knows to stop. Always end your answer with <br><br>"
        f"\n{suffix}"
    )

from typing import Literal

from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.prebuilt import create_react_agent
from langgraph.graph import MessagesState, END
from langgraph.types import Command


def get_next_node(last_message: BaseMessage, goto: str):
    #print(last_message.content)
    if "FINAL ANSWER" in last_message.content:
        print("LAST MESSAGE!")
        # Any agent decided the work is done
        return END
    return goto


# Research agent and node
research_agent = create_react_agent(
    llm,tools=[],
    state_modifier=make_system_prompt(
        "You can only do research and cannot do any other actions. Your goal is to find the right document snippets based on the user's query. You are working with a calculation colleague. The risk factor for someone with type 1 diabetes is 3 and the risk factor for tachicardia is 1. You also know the base premium is 100$"
    ),
)

calculation_agent = create_react_agent(
    llm,tools=[],
    state_modifier=make_system_prompt(
        "You can only calculate the insurance premium based on the information you are provided. The premiumn is calculated by multiplying the base premium by the risk factor"
    ),
)

def research_node(
    state: MessagesState,
) -> Command[Literal["calculator", END]]:
    result = research_agent.invoke(state)
    goto = get_next_node(result["messages"][-1], "calculator")
    # wrap in a human message, as not all providers allow
    # AI message at the last position of the input messages list
    result["messages"][-1] = HumanMessage(
        content=result["messages"][-1].content, name="researcher"
    )
    return Command(
        update={
            # share internal message history of research agent with other agents
            "messages": result["messages"],
        },
        goto=goto,
    )

def calculation_node(state: MessagesState) -> Command[Literal["researcher", END]]:
    result = calculation_agent.invoke(state)
    goto = get_next_node(result["messages"][-1], "researcher")
    # wrap in a human message, as not all providers allow
    # AI message at the last position of the input messages list
    result["messages"][-1] = HumanMessage(
        content=result["messages"][-1].content, name="calculator"
    )
    return Command(
        update={
            # share internal message history of chart agent with other agents
            "messages": result["messages"],
        },
        goto=goto,
    )

from langgraph.graph import StateGraph, START

workflow = StateGraph(MessagesState)
workflow.add_node("researcher", research_node)
workflow.add_node("calculator",calculation_node)
workflow.add_edge(START, "researcher")
graph = workflow.compile()

def call_graph():
    events = graph.stream(
    {
        "messages": [
            (
                "user",
                "First, find out the risk factor for someone with type 1 diabetes and a tachycardia. the base premium is 100$"
                "Then calculate the insurance premium by adding up all risk factors and multiplying it by the premium. Once you have it, you're done!",
            )
        ],
    },
    # Maximum number of steps to take in the graph
    {"recursion_limit": 10},
     stream_mode=['messages']
)
    return events