# used to send information from React frontend to Langgraph update workflow
from flask import Flask, request, jsonify
# from update_workflow import [used method for updating db]

app = Flask(__name__)

# get information regarding state of database
@app.route('/db', methods=['GET']) 
def get_db_state():
    db_state = None
    # fetch most recent upload, time range of first + last upload
    # fetch storage usage for both chromaDB + EC2, 
    return jsonify(db_state)

# pass changes inputted from react to langgraph
@app.route('/db', methods=['POST']) 
def handle_update():

    input = request.json.get('input')  # from react
    if not input:
        return jsonify({"error": "Input is required"}), 400

# Endpoint to get the staff list
@app.route('/api/staff', methods=['GET'])
def get_staff():
    staff_data = None
    #if stored as json locally, just get relative path and return JSON
    return jsonify(staff_data)

# Endpoint to update the staff list
@app.route('/api/staff', methods=['POST'])
def update_staff():
    new_staff_data = request.json
    staff_data.append(new_staff_data)
    return jsonify(new_staff_data), 201


if __name__ == '__main__':
    app.run(debug=True)