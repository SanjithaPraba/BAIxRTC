import slack
import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask
from slackeventsapi import SlackEventAdapter
import sys
sys.path.append("c:/Users/shriy/OneDrive/Desktop/Experiential/projects/BAIxRTC") 
from LangGraph.query_workflow import QueryState, retrieve_context, generate_response, should_respond, rag_bot

env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path) #load env vars

app = Flask(__name__)
slack_events_adapter = SlackEventAdapter(os.environ["SLACK_SIGNING_SECRET"], "/slack/events", app)

client = slack.WebClient(token=os.environ["SLACK_TOKEN"])
BOT_ID = client.api_call("auth.test")["user_id"]

#read + respond to msges
@slack_events_adapter.on('message')
def message(payload):
    event = payload.get('event', {})
    channel_id = event.get('channel')
    user_id = event.get('user')
    text = str(event.get('text'))
    thread_ts = event.get('ts') or event.get('thread_ts')

    question = QueryState(question=text)
    result_state = rag_bot.invoke(question)
    if BOT_ID != user_id:
        client.chat_postMessage(channel=channel_id, text=result_state.get("response"), thread_ts=thread_ts)

@app.route('/help', methods=['POST']) #command for intro for the slack bot
def help():
    return "This is RTC's Slack bot. You can ask me anything and I will try to help you."


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)