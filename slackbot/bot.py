import slack
import os, json
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask
from slackeventsapi import SlackEventAdapter
import sys
sys.path.append("c:/Users/shriy/OneDrive/Desktop/Experiential/projects/BAIxRTC") 
from LangGraph.query_workflow import QueryState, rag_bot

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path) #load env vars

ESCALATION_FILE = "escalation_schema.json"
app = Flask(__name__)
slack_events_adapter = SlackEventAdapter(os.environ["SLACK_SIGNING_SECRET"], "/slack/events", app)

client = slack.WebClient(token=os.environ["SLACK_TOKEN"])
BOT_ID = client.api_call("auth.test")["user_id"]

processed_events = set()

@slack_events_adapter.on('message')
def message(payload):
    event = payload.get('event', {})
    event_id = payload.get('event_id')
    user_id = event.get('user')

    if (event.get('subtype') == 'bot_message' or 
        user_id == BOT_ID or 
        user_id is None or 
        event_id in processed_events):
        return

    processed_events.add(event_id) #shld only respond once

    channel_id = event.get('channel')
    text = str(event.get('text'))
    thread_ts = event.get('ts') or event.get('thread_ts')

    question = QueryState(question=text)
    result_state = rag_bot.invoke(question)
    
    if result_state.get("response"):
        response = client.chat_postMessage(
            channel=channel_id,
            text=result_state.get("response"),
            thread_ts=thread_ts
        )
        timestamp = response['ts']
        client.reactions_add(channel=channel_id, name="smile", timestamp=timestamp)
        client.reactions_add(channel=channel_id, name="sob", timestamp=timestamp)

def load_escalation_date(): #load escalation schema json
    with open(ESCALATION_FILE, 'r') as file:
        escalation_data = json.load(file)
    return escalation_data

@slack_events_adapter.on('reaction_added')
def reaction_added(payload):
    event = payload.get('event', {})
    reaction = event.get('reaction')
    
    if reaction != 'sob':
        return  # only escalate on the correct reaction

    item = event.get('item', {})
    channel_id = item.get('channel')
    message_ts = item.get('ts')

    original_message = client.conversations_replies(channel=channel_id, ts=message_ts) #need this cuz the reaction is on the bot reply
    if not original_message['messages']:
        return

    bot_message = original_message['messages'][0]
    question_text = bot_message.get('text', '') 
   
    state = QueryState(question=question_text)
    result = rag_bot.invoke(state) 
    category = result.category 

    escalation_data = load_escalation_date()
    schema = escalation_data["escalation_schema"]
    category_data = schema[category]
    members = category_data["member_ids"]
    index = category_data["last_assigned_index"]

    next_index = (index + 1) % len(members)
    assigned_member = members[next_index]

    category_data["last_assigned_index"] = next_index
    with open(ESCALATION_FILE, 'w') as f:
        json.dump(escalation_data, f, indent=2)

    client.chat_postMessage(
        channel=channel_id,
        text=f"Escalating this to <@{assigned_member}> for **{category}**.",
        thread_ts=message_ts
    )


        
@app.route('/help', methods=['POST']) #command for intro for the slack bot
def help():
    return "This is RTC's Slack bot. You can ask me anything and I will try to help you."


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)