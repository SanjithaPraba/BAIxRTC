from common_workflow import QueryState, create_and_store_embedding, inspect_embeddings
from langgraph.graph import StateGraph
from database.schema_manager import SchemaManager
from pydantic import BaseModel

graph = StateGraph(QueryState)

# Define the state schema
class Update(BaseModel):
    question: str
    category: str | None = None
    response: str | None = None

# def store_and_inspect(state: QueryState):
#     state, ids = create_and_store_embedding(state)  # embed + store
#     inspect_embeddings(ids)  # view what was stored
#     return state

# uncomment if you don't want to inspect the embeddings that were uploaded
# graph.add_node("store_embeddings", create_and_store_embedding)

# included inspection and storing of embeddings

#create schemamanager
schema_manager = SchemaManager()

def process_and_upload_messages(state: QueryState, files):
    if (files):
        schema_manager.add_jsons() #upload msgs to aws db
        schema_manager.close_connection()
        state, ids = create_and_store_embedding(state)  #upload + embed to chromadb
    return state


graph.add_node("store_data", process_and_upload_messages)
graph.set_entry_point("store_data")
update_app = graph.compile()
#inputs = dictionary passed to langgraph by schema_manager
update_app.invoke(inputs)
