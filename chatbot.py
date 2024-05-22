import os
import requests
from datetime import timezone, datetime, timedelta
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from langchain.output_parsers.openai_tools import JsonOutputToolsParser

domain = 'https://api.calendly.com'
headers = {"Authorization": f'Bearer {os.environ['CALENDLY_API_TOKEN']}'}

from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

examples = [
    HumanMessage(
        "show me the scheduled events", name="example_user"
    ),
    AIMessage(
        "",
        name="example_assistant",
        tool_calls=[
            {"name": "get_user_uri", "args": {}, "id": "1"}
        ],
    ),
    ToolMessage("https://api.calendly.com/users/66cf2fc5-a315-48d3-affd-ff2f453d5e82", tool_call_id="1"),
    AIMessage(
        "",
        name="example_assistant",
        tool_calls=[{"name": "list_events", "args": {"user_uri": "https://api.calendly.com/users/66cf2fc5-a315-48d3-affd-ff2f453d5e82"}, "id": "2"}],
    ),
    ToolMessage('[["30 Minute Meeting", "2024-05-22T18:30:00.000000Z", "2024-05-22T19:00:00.000000Z"]]', tool_call_id="2"),
    AIMessage(
        "You have 1 30 minute meeting starting at 2024-05-22T18:30:00.000000Z and ending at 2024-05-22T19:00:00.000000Z",
        name="example_assistant",
    ),
    # delete event
    HumanMessage(
        "cancel my event at 8pm today", name="example_user_1"
    ),
    AIMessage(
        "",
        name="example_assistant_1",
        tool_calls=[
            {"name": "get_user_uri", "args": {}, "id": "3"}
        ],
    ),
    ToolMessage("https://api.calendly.com/users/66cf2fc5-a315-48d3-affd-ff2f453d5e82", tool_call_id="3"),
    AIMessage(
        "",
        name="example_assistant_1",
        tool_calls=[{"name": "cancel_event", "args": {"user_uri": "https://api.calendly.com/users/66cf2fc5-a315-48d3-affd-ff2f453d5e82", "start": "8pm"}, "id": "4"}],
    ),
    ToolMessage("Meeting Successfully Cancelled", tool_call_id="4"),
    AIMessage(
        "Meeting Successfully Cancelled",
        name="example_assistant_1",
    ),
    # fail delete
    HumanMessage(
        "cancel my event at 8pm today", name="example_user_2"
    ),
    AIMessage(
        "",
        name="example_assistant_2",
        tool_calls=[
            {"name": "get_user_uri", "args": {}, "id": "5"}
        ],
    ),
    ToolMessage("https://api.calendly.com/users/66cf2fc5-a315-48d3-affd-ff2f453d5e82", tool_call_id="5"),
    AIMessage(
        "",
        name="example_assistant_2",
        tool_calls=[{"name": "cancel_event", "args": {"user_uri": "https://api.calendly.com/users/66cf2fc5-a315-48d3-affd-ff2f453d5e82", "start": "8pm"}, "id": "6"}],
    ),
    ToolMessage("Meeting Failed to be Cancelled", tool_call_id="6"),
    AIMessage(
        "Meeting Failed to be Cancelled",
        name="example_assistant_1",
    ),
    # no mettings for time
    HumanMessage(
        "cancel my event at 8pm today", name="example_user_3"
    ),
    AIMessage(
        "",
        name="example_assistant_3",
        tool_calls=[
            {"name": "get_user_uri", "args": {}, "id": "7"}
        ],
    ),
    ToolMessage("https://api.calendly.com/users/66cf2fc5-a315-48d3-affd-ff2f453d5e82", tool_call_id="7"),
    AIMessage(
        "",
        name="example_assistant_3",
        tool_calls=[{"name": "cancel_event", "args": {"user_uri": "https://api.calendly.com/users/66cf2fc5-a315-48d3-affd-ff2f453d5e82", "start": "8pm"}, "id": "8"}],
    ),
    ToolMessage("No calendar event at that time", tool_call_id="8"),
    AIMessage(
        "There is no calendar event to be delted for given time",
        name="example_assistant_3",
    ),
]

system = """You are a an assitant that uses tools to help manage schedules. 

Use past tool usage as an example of how to correctly use the tools."""

few_shot_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        *examples,
        ("human", "{query}"),
    ]
)

@tool
def get_user_uri() -> str:
    """
    Gets current users user_uri

    """
    response = requests.get(f'{domain}/users/me', headers=headers)
    return response.json()['resource']['uri']


@tool
def list_events(user_uri) -> list[list[str]]:
    """
    Lists all calendar events for given user_uri

    Args:
        user_uri: first str

    """
    params = {'user': user_uri, 'status': 'active'}
    response = requests.get(f'{domain}/scheduled_events', headers=headers, params=params)
    formated_events = []
    for event in response.json()['collection']:
        formated_events.append([event['name'], event['start_time'], event['end_time']])
    return str(formated_events)



@tool
def cancel_event(user_uri, start) -> str:
    """
    Cancels event based on user_uri and start

    Args:
        event_uuid: first str
        start: second str
    """
    hour = 0
    if 'pm' in start.lower():
        hour = 12 + int(start[:-2])
    elif 'am' in start.lower():
        hour = int(start[:-2]) 
        
    now = datetime.now()
    dt = datetime(now.year, now.month, now.day, hour, 0, 0).astimezone()
    dt = dt.astimezone(timezone.utc)

    params = {'user': user_uri, 'min_start_time': dt.isoformat(), 'status': 'active'}
    response = requests.get(f'{domain}/scheduled_events', headers=headers, params=params)

    if response.json()['collection'] == [] or response.json()['collection'][0]['start_time'] != dt.isoformat(timespec='microseconds')[:-6] + 'Z':
        return "No calendar event at that time"
    

    event_uuid = response.json()['collection'][0]['uri'].split('/')[-1]

    response = requests.post(f'{domain}/scheduled_events/{event_uuid}/cancellation', headers=headers)

    if response.status_code == 201:
        return "Meeting Successfully Cancelled"
    return "Meeting Failed to be Cancelled " + str(response.json())


tools = [ cancel_event, get_user_uri, list_events]

llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.2, verbose=True)
llm = llm.bind_tools(tools)
chain = {"query": RunnablePassthrough()} | few_shot_prompt | llm


def invoke_chat_bot(query):
    messages = [HumanMessage(content=query)]
    ai_msg = chain.invoke(messages)
    messages.append(ai_msg)

    for tool_call in ai_msg.tool_calls:
        selected_tool = {"get_user_uri": get_user_uri, "list_events": list_events, "cancel_event": cancel_event}[tool_call["name"].lower()]
        tool_output = selected_tool.invoke(tool_call["args"])
        messages.append(ToolMessage(tool_output, tool_call_id=tool_call["id"]))


    for msg in messages:
        print(msg)

    return chain.invoke(messages).content
