from common_workflow import QueryState, create_and_store_embedding
from langgraph.graph import StateGraph

graph = StateGraph(QueryState)

graph.add_node("store_embeddings", create_and_store_embedding)
graph.set_entry_point("store_embeddings")

update_app = graph.compile()
