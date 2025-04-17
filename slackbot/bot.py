import slack
import os
import json
from pathlib import Path
from flask import Flask
from slackeventsapi import SlackEventAdapter
from slack_sdk import WebClient
from dotenv import load_dotenv
from LangGraph.query_workflow import QueryState, rag_bot

#load env vars
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

# flask + slack setup
app = Flask(__name__)
slack_events_adapter = SlackEventAdapter(os.environ["SLACK_SIGNING_SECRET"], "/slack/events", app)
client = WebClient(token=os.environ["SLACK_TOKEN"])
BOT_ID = client.api_call("auth.test")["user_id"]

# path to escalation schema file
ESCALATION_FILE = os.path.join(os.path.dirname(__file__), "escalation.json")

# utility functions
def load_escalation_data():
    with open(ESCALATION_FILE, 'r') as file:
        return json.load(file)

def update_escalation_data(data): # do we need this ..
    with open(ESCALATION_FILE, 'w') as f:
        json.dump(data, f, indent=2)

# ------- core logic ----------

# using QueryState + rag_bot to classify the question
# If it's a valid question (i.e., has a response), respond and react to the message.
def classify_and_respond_to_message(channel_id, text, thread_ts):
    question = QueryState(question=text)
    result = rag_bot.invoke(question)
    category = result.get("category")
    response = result.get("response")

    # query workflow will determine if it needs to respond to the message or not
    if response:
        # post the bot repl
        reply = client.chat_postMessage(
            channel=channel_id,
            text=response,
            thread_ts=thread_ts
        )
        # timestamp of the bots reply
        bot_ts = reply['ts']

        # adding emojis to bot reply
        client.reactions_add(channel=channel_id, name="smile", timestamp=bot_ts)
        client.reactions_add(channel=channel_id, name="sob", timestamp=bot_ts)

        # store category in message metadata (for dev only — not persistent)
        return bot_ts, category

    return None, None

# escalate a message to the appropriate member based on category.
def escalate_issue(channel_id, message_ts, category):
    escalation_data = load_escalation_data()
    schema = escalation_data.get("escalation_schema", {})

    if category not in schema:
        # DO NOT ACTUALLY SEND THIS TO SLACK LATER, LEAVING FOR DEBUGGING ATM
        client.chat_postMessage(
            channel=channel_id,
            text=f"Could not find escalation category for *{category}*.",
            thread_ts=message_ts
        )
        return

    category_data = schema[category]
    members = category_data["member_ids"]
    index = category_data["last_assigned_index"]
    next_index = (index + 1) % len(members)
    assigned_member = members[next_index]

    # rotating to next member (not terribly sure)
    category_data["last_assigned_index"] = next_index
    update_escalation_data(escalation_data)

    # ping the assigned member based on escalation json
    client.chat_postMessage(
        channel=channel_id,
        text=f"Escalating this to <@{assigned_member}> for *{category}* help.",
        thread_ts=message_ts
    )

# ------- event handling ----------
# tracking messages and bot replies for escalation mapping
bot_message_map = {}  # {bot_ts: category}

@slack_events_adapter.on("message")
def handle_message(payload):
    event = payload.get("event", {})
    user = event.get("user")
    text = event.get("text")
    thread_ts = event.get("ts")

    # only respond to user messages (not bots so we don't categorize our own bot's replies)
    if event.get("subtype") == "bot_message" or user == BOT_ID or user is None:
        return

    bot_ts, category = classify_and_respond_to_message(event["channel"], text, thread_ts)
    if bot_ts and category:
        bot_message_map[bot_ts] = category  # store for escalation YOOOO CHECK THIS LOGIC


@slack_events_adapter.on("reaction_added")
def handle_reaction(payload):
    event = payload.get("event", {})
    user = event.get("user")
    reaction = event.get("reaction")
    item = event.get("item", {})
    channel_id = item.get("channel")
    message_ts = item.get("ts")

    # ignore bot's own reactions
    if user == BOT_ID or reaction != "sob":
        return

    # if this reaction is on a bot message that we replied with, escalate
    if message_ts in bot_message_map:
        category = bot_message_map[message_ts]
        escalate_issue(channel_id, message_ts, category)
#
# current_question_text = None
# current_category = None
#
# processed_events = set()
#
# @slack_events_adapter.on('message')
# def message(payload):
#     global current_category, current_question_text
#
#     event = payload.get('event', {})
#     event_id = payload.get('event_id')
#     user_id = event.get('user')
#
#     if (event.get('subtype') == 'bot_message' or
#         user_id == BOT_ID or
#         user_id is None or
#         event_id in processed_events):
#         return
#
#     processed_events.add(event_id) #shld only respond once
#
#     channel_id = event.get('channel')
#     current_question_text = str(event.get('text'))
#     thread_ts = event.get('ts') or event.get('thread_ts')
#
#     question = QueryState(question=current_question_text)
#     result_state = rag_bot.invoke(question)
#     current_category = result_state.get("category")
#
#     if result_state.get("response"):
#         response = client.chat_postMessage(
#             channel=channel_id,
#             text=result_state.get("response"),
#             thread_ts=thread_ts
#         )
#         timestamp = response['ts']
#         client.reactions_add(channel=channel_id, name="smile", timestamp=timestamp)
#         client.reactions_add(channel=channel_id, name="sob", timestamp=timestamp)
#
#
# @slack_events_adapter.on('reaction_added')
# def reaction_added(payload):
#     global current_question_text,current_category
#
#     event = payload.get('event', {})
#     reaction = event.get('reaction')
#
#     if reaction != 'sob':
#         return  # only escalate on the correct reaction
#
#     item = event.get('item', {})
#     channel_id = item.get('channel')
#     message_ts = item.get('ts')
#
#     original_message = client.conversations_replies(channel=channel_id, ts=message_ts)
#     if not original_message['messages']:
#         return
#
#     message = original_message['messages'][0]
#     print(message)
#     question_text = message.get('text', '')
#
#     state = QueryState(question=question_text)
#     result = rag_bot.invoke(state)
#     category = message.get("category")
#     print(category)
#
#     escalation_data = load_escalation_date()
#     schema = escalation_data["escalation_schema"]
#
#     # match category exactly (or use case-insensitive matching if needed)
#     if category not in schema:
#         client.chat_postMessage(
#             channel=channel_id,
#             text=f"Sorry, I couldn't find an escalation category for **{category}**.",
#             thread_ts=message_ts
#         )
#         return
#
#     category_data = schema[category]
#     members = category_data["member_ids"]
#     index = category_data["last_assigned_index"]
#
#     next_index = (index + 1) % len(members)
#     assigned_member = members[next_index]
#
#     # update the index
#     category_data["last_assigned_index"] = next_index
#
#     with open(ESCALATION_FILE, 'w') as f:
#         json.dump(escalation_data, f, indent=2)
#
#     client.chat_postMessage(
#         channel=channel_id,
#         text=f"Escalating this to <@{assigned_member}> for **{category}**.",
#         thread_ts=message_ts
#     )

        
@app.route('/help', methods=['POST']) #command for intro for the slack bot
def help():
    return "This is RTC's Slack bot. You can ask me anything and I will try to help you."


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=3000)