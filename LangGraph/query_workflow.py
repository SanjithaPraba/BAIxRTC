from langgraph.graph import StateGraph
from .common_workflow import QueryState, should_respond, retrieve_context, generate_response

graph = StateGraph(QueryState)

graph.add_node("should_respond", should_respond)
graph.add_node("retrieve_context", retrieve_context)
graph.add_node("respond", generate_response)

graph.set_entry_point("should_respond")

# edges differ if the query should actually be responded to by the LLM!
def route_response(state: QueryState) -> str:
    return "retrieve_context" if state.category == "should_respond" else "end"

graph.add_conditional_edges("should_respond", route_response, {
    "retrieve_context": "retrieve_context",
    "end": "__end__"
})

graph.add_edge("retrieve_context", "respond")

rag_bot = graph.compile()

# Example: Running the workflow
def test_query_workflow():
    # intended to be a message that the llm DOES NOT respond to
    # input_question = QueryState(question="I know that RTC has certain affinity groups. I will DM you the information needed.")
    # intended to be a message that the llm DOES respond to
    input_question = QueryState(question="Does RTC have any affinity groups? If so, for what groups?")
    response = rag_bot.invoke(input_question)
    print(response.get("response"))

if __name__ == "__main__":
    test_query_workflow()