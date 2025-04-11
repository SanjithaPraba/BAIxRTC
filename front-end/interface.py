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


@app.route("/api/staff", methods=["GET"])
def get_staff_list():
    json_path = os.path.join(os.path.dirname(__file__), "..", "database", "task_escalation.json")

    with open(json_path, "r") as file:
        data = json.load(file)

    escalation_schema = data["escalation_schema"]
    staff_dict = {}

    for task, assignees in escalation_schema.items(): #assignees = staff for that task (category)
        member_ids = assignees["member_ids"]
        member_names = assignees["member_names"]

        for i in range(len(member_ids)):
            member_id = member_ids[i]
            member_name = member_names[i]

            if member_id not in staff_dict:
                staff_dict[member_id] = {
                    "name": member_name,
                    "tasks": [],
                    "accountId": member_id
                }

            staff_dict[member_id]["tasks"].append(task)

    # Convert tasks list to a comma-separated string
    staff_list = []
    for staff in staff_dict.values():
        staff["tasks"] = ", ".join(staff["tasks"])
        staff_list.append(staff)

    return jsonify(staff_list)

@app.route("/api/staff", methods=["POST"])
def update_staff_list():
    try:
        staff_list = request.get_json()
        print(staff_list)

        # Initialize the escalation schema dictionary
        escalation_schema = {}

        for member in staff_list:
            name = member["name"]
            account_id = member["accountId"]
            # Convert comma-separated string to list
            tasks = [task.strip() for task in member["tasks"].split(",")]
            print(name)

            for task in tasks:
                if task not in escalation_schema:
                    escalation_schema[task] = {
                        "member_ids": [],
                        "member_names": [],
                        "last_assigned_index": 0
                    }
        
                if account_id not in escalation_schema[task]["member_ids"]:
                    escalation_schema[task]["member_ids"].append(account_id)

                if name not in escalation_schema[task]["member_names"]:
                    escalation_schema[task]["member_names"].append(name)

        # Write to tasks.json
        filepath = os.path.join(os.path.dirname(__file__), "../database/task_escalation.json")
        with open(filepath, "w") as f:
            json.dump(escalation_schema, f, indent=2)

        return jsonify({"message": "Task escalation schema updated successfully."}), 200

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)