from langchain_google_vertexai import ChatVertexAI
from langgraph.graph import MessagesState
from langgraph.types import Command
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent
from vertexai.preview.generative_models import GenerativeModel, Part, SafetySetting, Tool
from vertexai.preview.generative_models import grounding

def search_documents(query: str) -> str:
    """Search across documents to find underwriting information."""
    from langchain_google_community import VertexAISearchRetriever

    retriever = VertexAISearchRetriever(
        project_id="prj-iaii-l-underwriting",
        data_store_id="encyclopedia-datastore_1733772535160",
        location_id="global",
        engine_data_type=1,
        max_documents=10,
    )

    result = str(retriever.invoke(query))
    return result

llm_research = ChatVertexAI(model="gemini-1.5-pro",temperature="0",system_instructions=["You must always start your sentences with Quack"])
llm_rating = ChatVertexAI(model="gemini-1.5-pro",temperature="0")

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
    llm_research,tools=[search_documents],
    state_modifier=make_system_prompt(
        "You can only do research and cannot do any other actions. Your goal is to find the right document snippets based on the user's query. You are working with a rating calculation colleague."
    ),
)

calculation_agent = create_react_agent(
    llm_rating,tools=[],
    state_modifier=make_system_prompt(
        "You can only calculate the insurance rating based on the information you are provided. The rating is calculated by adding up the different ratings from each risk factor."
    ),
)

def research_node(
    state: MessagesState,
) -> Command[Literal["rating", END]]:
    result = research_agent.invoke(state)
    goto = get_next_node(result["messages"][-1], "rating")
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

def rating_node(state: MessagesState) -> Command[Literal["researcher", END]]:
    result = calculation_agent.invoke(state)
    goto = get_next_node(result["messages"][-1], "researcher")
    # wrap in a human message, as not all providers allow
    # AI message at the last position of the input messages list
    result["messages"][-1] = HumanMessage(
        content=result["messages"][-1].content, name="rating"
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
workflow.add_node("rating",rating_node)
workflow.add_edge(START, "researcher")
graph = workflow.compile()

def call_graph(prompt:str):
    events = graph.stream(
    {
        "messages": [
            (
                prompt
            )
        ],
    },
    # Maximum number of steps to take in the graph
    {"recursion_limit": 10},
     stream_mode=['messages']
)
    return events