# used to send information from React frontend to Langgraph update workflow
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
# from update_workflow import [used method for updating db]
from datetime import datetime #get class from module - used to convert timsestamps
from database.schema_manager import SchemaManager

app = Flask(__name__)
CORS(app)

# get information regarding state of database
@app.route('/api/db', methods=['GET']) 
def get_db_state():
    db_state = {}
    #might have to store latest upload time in localstorage lol
 
    # fetch time range of first + last upload + convert from ts to utc
    schema_manager = SchemaManager()
    first_date, last_date = schema_manager.get_timerange()
    schema_manager.close_connection()
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
    #upload files to rtc_data, langgraph will run processing + upload scripts 
    files = request.files.getlist("jsonExport")
    new_upload = False
    if (len(files) > 0):
        new_upload = True
        for file in files:
            file.save(os.path.join("rtc_data", file.filename))

    #put in rtc_data, start langgraph flow   
    auto_upload = request.form.get("autoUpload") == "true" #formdata forces it to be a string

    #get dates for deletion - both will be "" or "YYYY-MM-DD"
    delete_from = request.json.get('deleteFrom')  
    delete_to = request.json.get('deleteTo') 
    #convert dates to timestamp for db parsing 
    delete_from_ts = date_to_unix(delete_from)
    delete_to_ts = date_to_unix(delete_to, end_of_day=True)

    #call langgraph update workflow 
        #build the querystate
        #import the compiled workflow
        #invoke the workflow with the querystate

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