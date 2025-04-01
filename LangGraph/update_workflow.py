from common_workflow import QueryState, create_and_store_embedding, inspect_embeddings
from langgraph.graph import StateGraph

graph = StateGraph(QueryState)

def store_and_inspect(state: QueryState):
    state, ids = create_and_store_embedding(state)  # embed + store
    inspect_embeddings(ids)  # view what was stored
    return state

# uncomment if you don't want to inspect the embeddings that were uploaded
# graph.add_node("store_embeddings", create_and_store_embedding)

# included inspection and storing of embeddings
graph.add_node("store_embeddings", store_and_inspect)
graph.set_entry_point("store_embeddings")

update_app = graph.compile()
