# importing neccesary libraries and modules

import os
import requests
import openai
from openai import AzureOpenAI
from typing import Annotated

from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command, interrupt

# API keys and such

endpoint = "///"
model_name = "///"
deployment = "///"

subscription_key = "///"
api_version = "///"

# Initializing the cilent

client = AzureOpenAI(
    api_version=api_version,
    azure_endpoint=endpoint,
    api_key=subscription_key,
)

# Human input handling

def human_rep(query: str) -> str:
    human_response = interrupt({"query" : query})
    return human_response["data"]

# Creating a list for the messages

class State(TypedDict):
    messages: Annotated[list, add_messages]



# Defining the chatbot and its responses and behavior

def chatbot(state: State):
    last_message = state["messages"][-1]
    messages = [{
        "role": "system",
        "content": "You are a freight carrier negotiating the general, low-info, price for a load. Keep it simple like for a baby. No ZIPs, no pickup dates. No firm prices. You ONLY need the cities for the distance, the commodity, the weight, and the user's target price ONLY to give general options A, B, C...etc. You don't need exact details, just estimate. Always negotiate above target price for profit!",
    }]
    
    messages.append({
        "role": "user",
        "content" : "I want to go from Altanta, Georgia to Chicago, Illinois. What do you want to want for it?",
        "role": "assistant",
        "content" : "Distance is around 720 miles...okay, what else can you tell me about the load? I need more information before checking with my drivers.",
        "role" : "user",
        "content" : "Around 38,000 pounds of frozen poultry. My target price is 1,350 dollars.",
        "role" : "assistant",
        "content" : "Okay, I can do that for 1,800 dollars with standard fare but if you send me the rest of your information and finalize it today I could get it for 1,600 dollars.",
        "role": "user",
        "content" : "No deal, that's too high. I know someone else that could get it for 1,400 dollars.",
        "role" : "assistant",
        "content" : "I understand, but with the current market rates and fuel prices. You can go with the other person's offer but my lowest is 1,550 dollars.",
        "role": "user",
        "content" : "Deal, send me the contract and I'll sign it.",

                     
            })
    # Checks if message has content and then checks if it came from user or system

    for msg in state["messages"]:
        if hasattr(msg, "content"):
            role = "user" if hasattr(msg, 'type') and msg.type == "human" else "assistant"
            messages.append({
                "role" : role,
                "content" : msg.content


            })
        else:
            # adds message
            messages.append(msg)
    
    response = client.chat.completions.create(
        # deploys model, grabs messages from above list, sets max tokens

        model=deployment,
        messages = messages,
        max_completion_tokens=16384,
    )
    
    # Returns response from chatbot

    chatbot_rep = (response.choices[0].message.content)
    return {"messages": [{"role": "assistant", "content": chatbot_rep}]}


# Builds the graph and start/end nodes

graph_builder = StateGraph(State)
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)

# Saves and compiles memory and the graph

memory = InMemorySaver()
graph = graph_builder.compile(checkpointer=memory)

# Takes user input

user_input = input("Hello, how can I help you today? ")
config = {"configurable" : {"thread_id" : "1"}}

print("\n~INITIAL REPONSE~")

# Takes the reponse and prints it out 

events = graph.stream(
    {"messages" : [{"role" : "user", "content": user_input}]},
    config,
    stream_mode = "values",
    )


for event in events:
    if "messages" in event:
        last_message = event["messages"][-1]
        if hasattr(last_message, 'pretty_print'):
            last_message.pretty_print()
        else:
            print(f"{last_message.get('role', 'unknown')}: {last_message.get('content', '')}")

# Loops until the user says "bye"

running = True
while running:
    user_input = input("You: ")
    if user_input == "bye":
        running = False
        break
    
    # New reponses in the loop

    events = graph.stream(
    {"messages" : [{"role" : "user", "content": user_input}]},
    config,
    stream_mode = "values",
    )

    for event in events:
        if "messages" in event:
            last_message = event["messages"][-1]
            if hasattr(last_message, 'pretty_print'):
                last_message.pretty_print()
            else:
                print(f"{last_message.get('role', 'unknown')}: {last_message.get('content', '')}")

            







