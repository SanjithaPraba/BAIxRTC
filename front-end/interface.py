# used to send information from React frontend to Langgraph update workflow
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from LangGraph.update_workflow import invoke_update
from datetime import datetime #get class from module - used to convert timsestamps
from database.schema_manager import SchemaManager

app = Flask(__name__)
# CORS(app)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})

# get information regarding state of database
@app.route('/api/db', methods=['GET']) 
def get_db_state():
    db_state = {}
    #might have to store latest upload time in localstorage lol
 
    # fetch time range of first + last upload + convert from ts to utc
    schema_manager = SchemaManager()
    first_date, last_date = schema_manager.get_timerange()
    schema_manager.close_connection()
    if not first_date or not last_date:
        return jsonify({"error": "No data found in database"}), 404
    first_dt = datetime.fromtimestamp(int(float(first_date)))
    last_dt = datetime.fromtimestamp(int(float(last_date)))
    # turn into strings
    first_str = first_dt.strftime("%m/%d/%Y")
    last_str = last_dt.strftime("%m/%d/%Y")
    # compile strings
    date_range = f"{first_str} - {last_str}"
    db_state["dateRange"] = date_range

    # fetch storage usage for both chromaDB + EC2, 

    return jsonify(db_state)

# pass changes inputted from react to langgraph
@app.route('/api/db', methods=['POST'])
def handle_update():
    # 1. save the uploaded files to rtc_data
    uploaded_files = request.files.getlist("jsonExport")
    saved_file_paths = []
    should_upload = bool(uploaded_files)


    if uploaded_files:
        for file in uploaded_files:
            save_path = os.path.join("rtc_data", file.filename)
            file.save(save_path)
            saved_file_paths.append(save_path)

    # 2. get the form data values
    delete_from = request.form.get("deleteFrom") # these are now set to booleans
    delete_to = request.form.get("deleteTo")
    should_delete = bool(delete_from and delete_to)

    # 3. convert to timestamps
    delete_from_ts = date_to_unix(delete_from) if delete_from else None
    delete_to_ts = date_to_unix(delete_to, end_of_day=True) if delete_to else None

    # 4. open saved files as file-like objects (simulate FileStorage-like so update_workflow can invoke properly)
    file_objects = []
    try:
        for path in saved_file_paths:
            f = open(path, "rb")  # opened in binary mode
            file_objects.append(f)

        # 5. Call LangGraph workflow with opened files
        result = invoke_update(
            json_files=uploaded_files if should_upload else [],
            delete_from=delete_from_ts if should_delete else None,
            delete_to=delete_to_ts if should_delete else None
        )

    finally:
        # 6. cleanup the file handles
        for f in file_objects:
            f.close()

    return jsonify(result)

def date_to_unix(date_str, end_of_day=False):
    if not date_str:
        return ""
    dt_format = "%Y-%m-%d" #format of input string
    if end_of_day:
        dt = datetime.strptime(date_str, dt_format).replace(hour=23, minute=59, second=59) #add on until EOD to date
    else:
        dt = datetime.strptime(date_str, dt_format).replace(hour=0, minute=0, second=0) # add on midnight to date
    return int(dt.timestamp())  # Unix timestamp in seconds



@app.route("/api/staff", methods=["GET"])
def get_staff_list():
    print("✅ /api/staff endpoint was hit")

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
            tasks = [task.strip() for task in member["tasks"].split(",")]
            print(name)

            for task in tasks:
                if task not in escalation_schema:
                    escalation_schema[task] = {
                        "member_ids": [],
                        "member_names": []
                    }

                if account_id not in escalation_schema[task]["member_ids"]:
                    escalation_schema[task]["member_ids"].append(account_id)

                if name not in escalation_schema[task]["member_names"]:
                    escalation_schema[task]["member_names"].append(name)

        # Wrap it inside the top-level key "escalation_schema"
        wrapped_schema = {
            "escalation_schema": escalation_schema
        }

        # Write to task_escalation.json
        filepath = os.path.join(os.path.dirname(__file__), "../database/task_escalation.json")
        with open(filepath, "w") as f:
            json.dump(wrapped_schema, f, indent=2)

        return jsonify({"message": "Task escalation schema updated successfully."}), 200

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)