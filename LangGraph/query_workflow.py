from langgraph.graph import StateGraph
from common_workflow import QueryState, retrieve_context, generate_response

graph = StateGraph(QueryState)

graph.add_node("retrieve_context", retrieve_context)
graph.add_node("respond", generate_response)

graph.set_entry_point("retrieve_context")
graph.add_edge("retrieve_context", "respond")

rag_bot = graph.compile()

# Example: Running the workflow
def test_query_workflow():
    input_question = QueryState(question="Does RTC have affinity groups? If so, for what groups?")
    response = rag_bot.invoke(input_question)
    print(response)

if __name__ == "__main__":
    test_query_workflow()