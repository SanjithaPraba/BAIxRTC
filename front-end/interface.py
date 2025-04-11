# used to send information from React frontend to Langgraph update workflow
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
# from update_workflow import [used method for updating db]

app = Flask(__name__)
CORS(app)

# get information regarding state of database
@app.route('/api/db', methods=['GET']) 
def get_db_state():
    db_state = None
    # fetch most recent upload, time range of first + last upload
    # fetch storage usage for both chromaDB + EC2, 
    #fetch current json for staff info
    return jsonify(db_state)

# pass changes inputted from react to langgraph
@app.route('/api/db', methods=['POST']) 
def handle_update():
    # get values 
    json_export = request.json.get('jsonExport')
    #put in rtc_data, start langgraph flow   
    auto_upload = request.json.get('autoUpload')  
    delete_from = request.json.get('deleteFrom')  
    delete_to = request.json.get('deleteTo') 
    #get staff info
    handle_db_update()

def handle_db_update():
    #handle json
        #either export schema_manager.py add_json function
        #or add json to folder - how are processes being run?
    #handle deletion
        #schema_manager.py? or honestly directly connect to db and delete messages 
    #handle upload
        #langgraph 
    return 

#json_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../database/tasks_escalation.json"))

@app.route('/api/staff', methods=['GET'])
def get_staff_list():
    # Get the full path of the current file (interface.py)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Now go up one level and then into the 'database' directory
    json_path = os.path.join(base_dir, "..", "database", "task_escalation.json")

    print(f"Looking for tasks.json at: {json_path}")  # To debug the path
    try:
        with open(json_path, "r") as f:
            raw_data = json.load(f)
    except FileNotFoundError:
        return jsonify({"error": "tasks.json not found"}), 404
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON format"}), 500
    
    # Convert tasks list to comma-separated string
    formatted_data = []
    for entry in raw_data:
        formatted_data.append({
            "name": entry.get("name", ""),
            "tasks": ", ".join(entry.get("tasks", [])),
            "accountId": entry.get("accountId", "")
        })
    return jsonify(formatted_data)

@app.route('/api/staff', methods=['POST'])
def update_staff_list():
    #delimit the tasks by comma
    #change staff task json using fwrite
    return


if __name__ == '__main__':
    app.run(debug=True)