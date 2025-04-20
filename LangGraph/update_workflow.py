from .common_workflow import create_and_store_embedding, delete_chroma_by_date
from langgraph.graph import StateGraph, END
from database.schema_manager import SchemaManager
import json
from pydantic import BaseModel
from typing import List

# Define the update state schema
class UpdateState(BaseModel):
    json_files: List  # will contain Werkzeug FileStorage objects from Flask
    delete_from: str | None = None
    delete_to: str | None = None
    postgres_success: bool | None = None
    chroma_success: bool | None = None

    #For summary tracking
    deleted_postgres_count: int = 0
    deleted_chroma_count: int = 0
    inserted_postgres_count: int = 0
    inserted_chroma_count: int = 0

def update_chroma_db(state):
    if not state.json_files:
        print("Skipping Chroma upload: no files provided.")
        return state
    try:
        create_and_store_embedding(state.json_files)
        state.chroma_success = True
    except Exception as e:
        print(f"[Chroma Update Error]: {e}")
        state.chroma_success = False
    return state

def update_postgres_db(state: UpdateState) -> UpdateState:
    if not state.json_files:
        print("Skipping Postgres upload: no files provided.")
        return state
    schema_manager = None
    try:
        schema_manager = SchemaManager()
        inserted = 0

        for file in state.json_files:
            file.seek(0)  # make sure file pointer is at the start
            raw_json = file.read().decode("utf-8")
            messages = json.loads(raw_json)

            for message in messages:
                schema_manager.insert_message(message)
                inserted += 1

        state.inserted_postgres_count = inserted
        state.postgres_success = True
        schema_manager.connection.commit()  # commit to db
        print(f"✅ Inserted {inserted} messages into PostgreSQL.")
    except Exception as e:
        print(f"[Postgres Update Error]: {type(e).__name__} - {e}")
        state.postgres_success = False
    finally:
        schema_manager.close_connection()  # close the connection

    return state

def delete_postgres_node(state: UpdateState) -> UpdateState:
    if not (state.delete_from and state.delete_to):
        print("Skipping Postgres deletion: no date range provided.")
        return state
    try:
        if state.delete_from and state.delete_to:
            schema_manager = SchemaManager()
            row_count = schema_manager.delete_messages(state.delete_from, state.delete_to)
            state.deleted_postgres_count = row_count
            schema_manager.connection.commit()  # ensure deletion is committed
            schema_manager.close_connection()
            print("Deleted old messages from Postgres.")
    except Exception as e:
        print(f"[Postgres Delete Error]: {e}")
    return state

def delete_chroma_node(state: UpdateState) -> UpdateState:
    if not (state.delete_from and state.delete_to):
        print("Skipping Chroma deletion: no date range provided.")
        return state
    try:
        if state.delete_from and state.delete_to:
            count = delete_chroma_by_date(state.delete_from, state.delete_to)
            state.deleted_chroma_count = count
        state.chroma_success = None  # not a failure, just delete phase
    except Exception as e:
        print(f"[Chroma Delete Error]: {e}")
    return state

graph = StateGraph(UpdateState)
graph.add_node("delete_postgres", delete_postgres_node)
graph.add_node("delete_chroma", delete_chroma_node)
graph.add_node("update_postgres", update_postgres_db)
graph.add_node("update_chroma", update_chroma_db)

graph.set_entry_point("delete_postgres")
graph.add_edge("delete_postgres", "delete_chroma")
graph.add_edge("delete_chroma", "update_postgres")
graph.add_edge("update_postgres", "update_chroma")
graph.add_edge("update_chroma", END)

update_bot = graph.compile()

def invoke_update(json_files, delete_from, delete_to):
    state = UpdateState(
        json_files=json_files,
        delete_from=delete_from,
        delete_to=delete_to,
    )
    return update_bot.invoke(state)