# used to send information from React frontend to Langgraph update workflow
from flask import Flask, request, jsonify
from flask_cors import CORS
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

@app.route('/api/staff', methods=['GET'])
def get_staff_list():
    #change staff task json using fwrite
    return

@app.route('/api/staff', methods=['POST'])
def update_staff_list():
    #change staff task json using fwrite
    return


if __name__ == '__main__':
    app.run(debug=True)