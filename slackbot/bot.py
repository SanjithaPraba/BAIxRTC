import slack
import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask
from slackeventsapi import SlackEventAdapter
import sys
sys.path.append("c:/Users/shriy/OneDrive/Desktop/Experiential/projects/BAIxRTC") 
from LangGraph.common_workflow import QueryState, retrieve_context, generate_response, should_respond

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path) #load env vars

app = Flask(__name__)
slack_events_adapter = SlackEventAdapter(os.environ["SLACK_SIGNING_SECRET"], "/slack/events", app)

client = slack.WebClient(token=os.environ["SLACK_TOKEN"])
BOT_ID = client.api_call("auth.test")["user_id"]

@slack_events_adapter.on('message')
def message(payload):
    event = payload.get('event', {})
    channel_id = event.get('channel')

    client.chat_postMessage(channel=channel_id, text="Hello! I'm here to help you.")

@app.route('/help', methods=['POST']) #command for intro for the slack bot
def help():
    return "This is RTC's Slack bot. You can ask me anything and I will try to help you."


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)