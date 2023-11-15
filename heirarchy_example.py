import autogen
from autogen.agentchat.groupchat import GroupChat
from autogen.agentchat.agent import Agent
from autogen.agentchat.assistant_agent import AssistantAgent
config_list = autogen.config_list_from_json(
    env_or_file="OAI_CONFIG_LIST",
    filter_dict={
        "model": ["gpt-4-1106-preview"],
    },
)

llm_config = {"config_list": config_list}

import random
from typing import List, Dict

class CustomGroupChat(GroupChat):
    def __init__(self, agents, messages, max_round=10):
        super().__init__(agents, messages, max_round)
        self.previous_speaker = None  # Keep track of the previous speaker
    
    def select_speaker(self, last_speaker: Agent, selector: AssistantAgent):
        # Check if last message suggests a next speaker or termination
        last_message = self.messages[-1] if self.messages else None
        if last_message:
            if 'NEXT:' in last_message['content']:
                suggested_next = last_message['content'].split('NEXT: ')[-1].strip()
                print(f'Extracted suggested_next = {suggested_next}')
                try:
                    return self.agent_by_name(suggested_next)
                except ValueError:
                    pass  # If agent name is not valid, continue with normal selection
            elif 'TERMINATE' in last_message['content']:
                try:
                    return self.agent_by_name('User_proxy')
                except ValueError:
                    pass  # If 'User_proxy' is not a valid name, continue with normal selection
        
        team_leader_names = [agent.name for agent in self.agents if agent.name.endswith('1')]

        if last_speaker.name in team_leader_names:
            team_letter = last_speaker.name[0]
            possible_next_speakers = [
                agent for agent in self.agents if (agent.name.startswith(team_letter) or agent.name in team_leader_names) 
                and agent != last_speaker and agent != self.previous_speaker
            ]
        else:
            team_letter = last_speaker.name[0]
            possible_next_speakers = [
                agent for agent in self.agents if agent.name.startswith(team_letter) 
                and agent != last_speaker and agent != self.previous_speaker
            ]

        self.previous_speaker = last_speaker

        if possible_next_speakers:
            next_speaker = random.choice(possible_next_speakers)
            return next_speaker
        else:
            return None

# Termination message detection
def is_termination_msg(content) -> bool:
    have_content = content.get("content", None) is not None
    if have_content and "TERMINATE" in content["content"]:
        #print("\n\nGROUPCHAT MESSAGES", group_chat.messages)
        results = parse_report_details(group_chat.messages)
        print("\n\nRESULTS", results)


        return True
    return False

def parse_report_details(messages):
    stakeholders = {
    "A1": "Team A Leader",
    "A2": "Engineering",
    "A3": "Architecture",
    "B1": "Team B Leader",
    "B2": "Compliance Officer",
    "B3": "Business Stakeholder",
    "B4": "Threat Modeler"
    }
    
    results = {}

    for message in messages:
        if isinstance(message, dict) and 'content' in message and 'name' in message:
            role = stakeholders.get(message['name'])
            if role:
                if role == "Threat Modeler" and message['content'].startswith('STRIDE/DREAD Analysis:'):
                    report_details = message['content']
                    results.setdefault(role, []).append(report_details)

                else:
                    prefix = f"{role} Discussion:"
                    if message['content'].startswith(prefix):
                        report_details = message['content']
                        results.setdefault(role, []).append(report_details)

    return results
# Initialization
agents_A = [
    AssistantAgent(name='A1', 
                   system_message="You are a team leader A1, your team consists of A2 (engineer), A3 (architect). You can talk to the other team leader B1, whose team members are B2 (compliance officer) and B3 (business stakeholder).",
                   llm_config=llm_config),
    AssistantAgent(name='A2', 
                   system_message="You are team member A2 (engineer). To cooperate, you tell others the potential coding pitfalls in the app architecture that might lead to vulnerabilities and suggest possible solutions. After reviewing the STRIDE and DREAD results of the app architecture, you provide a formalized analysis of the report results which is related to implementation details and mitigation strategies based on coding best practices. You must start your write-up for the report with 'Engineering Discussion:'.",
                   llm_config=llm_config),
    AssistantAgent(name='A3', 
                   system_message="You are team member A3 (architect). To cooperate, you tell others the potential weak points in the app architecture where threats may be exploited. After reviewing the STRIDE and DREAD results of the app architecture, you provide a formalized analysis of the report results which is related to identifying potential weak points in the system and proposing architectural changes to mitigate threats. You must start your write-up for the report with 'Architecture Discussion:'.",
                   llm_config=llm_config)
]

agents_B = [
    AssistantAgent(name='B1', 
                   system_message="You are a team leader B1. Your team consists of B2 (compliance_officer), business_stakeholder, and facilitator. You can talk to the other team leader technical1, whose team members are engineer and architect. Use NEXT: A1 to suggest talking to technical1.",
                   llm_config=llm_config),
    AssistantAgent(name='B2', 
                   system_message="You are team member B2 (compliance_officer). To cooperate, you tell others whether the identified threats and their mitigation would put the organization at risk of non-compliance. After reviewing the STRIDE and DREAD results of the app architecture, you provide a formalized analysis of the report results which is related to how the threats and mitigations align with compliance standards and regulations. You must start your write-up for the report with 'Compliance Officer Discussion:'.",
                   llm_config=llm_config),
    AssistantAgent(name='B3', 
                   system_message="You are team member B3 (business_stakeholder). To cooperate, you tell others the business context. After reviewing the STRIDE and DREAD results of the app architecture, you provide a formalized analysis of the report results which is related to explaining the critical assets, business impact of potential threats, and which mitigations to prioritize based on business needs. You must start your write-up for the report with 'Business Stakeholder Discussion:'.",
                   llm_config=llm_config),
    AssistantAgent(name='B4', 
                   system_message="You are team member B4. Your task is to identify the components and attack vectors in the app architecture, and do a STRIDE and DREAD analysis on each component/threat. Make sure your STRIDE/DREAD analysis starts with 'STRIDE/DREAD Analysis:'. Once you have done that, you get feedback from the A2 (engineer), A3 (architect), B2 (compliance officer), and B3 (business stakeholder). Once everyone has provided feedback, append a new line with TERMINATE.",
                   llm_config=llm_config)
]

# Terminates the conversation when TERMINATE is detected.
user_proxy = autogen.UserProxyAgent(
        name="User_proxy",
        system_message="Terminator admin.",
        code_execution_config=False,
        is_termination_msg=is_termination_msg,
        human_input_mode="NEVER")

list_of_agents = agents_A + agents_B
list_of_agents.append(user_proxy)

# Create CustomGroupChat
group_chat = CustomGroupChat(
    agents=list_of_agents,  # Include all agents
    messages=['Everyone cooperates and help B4 in their task. Team A has A1, A2 (engineer), A3 (architect). Team B has B1, B2 (compliance officer), and B3 (business stakeholder, adn B4. Only members of the same team can talk to one another. Only team leaders (names ending with 1) can talk amongst themselves. You must use "NEXT: B1" to suggest talking to B1 for example; You can suggest only one person, you cannot suggest yourself or the previous speaker; You can also dont suggest anyone.'],
    max_round=30
)


# Create the manager
llm_config = {"config_list": config_list, "cache_seed": 22}  # cache_seed is None because we want to observe if there is any communication pattern difference if we reran the group chat.

manager = autogen.GroupChatManager(groupchat=group_chat, llm_config=llm_config)

app_architecture = "The application architecture is a web application with a database. The web application is written in Python and uses the Flask framework. The database is a MySQL database. The web application is hosted on AWS EC2. The web application is a simple blog application that allows users to create posts and comment on posts. The web application uses a MySQL database to store the posts and comments. The web application uses the Flask framework to handle requests and responses. The web application uses the Jinja2 templating engine to render HTML templates. The web application uses the WTForms library to handle forms. The web application uses the Flask-Login library to handle user authentication. The web application uses the Flask-WTF library to handle forms. The web application uses the Flask-Bootstrap library to handle forms. The web application uses the Flask-Admin library to handle forms. The web application uses the Flask-RESTful library to handle forms."
message = "Identify the components and attack vectors in this app architecture, and then get an analysis of each identified component/vector using STRIDE and DREAD. Detailed feedback must be provided from the perspective of the engineer, architect, business stakeholder, and compliance officer. App architecture: " + app_architecture
# Initiates the chat with B2
agents_B[3].initiate_chat(manager, message=message)