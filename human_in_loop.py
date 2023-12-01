import autogen
from autogen.agentchat.groupchat import GroupChat
from autogen.agentchat.agent import Agent
from autogen.agentchat.assistant_agent import AssistantAgent
import random
from typing import List, Dict
import sys

class DualOutput:
    def __init__(self, filename):
        self.terminal = sys.stdout
        self.log = open(filename, "w")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
        self.log.flush()

    def flush(self):
        # This flush method is needed for compatibility with the standard output.
        self.terminal.flush()
        self.log.flush()

config_list = autogen.config_list_from_json(
    "OAI_CONFIG_LIST",
    file_location="./",
    filter_dict={
        "model": ["gpt-4-1106-preview"],
    },
)

llm_config = {"config_list": config_list}

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
        return True
    return False

# Initialization
agents_A = [
    AssistantAgent(name='A1', 
                   system_message="You are a team leader A1, your team consists of A2 (engineer), A3 (architect). You can talk to the other team leader B1, whose team members are B2 (compliance officer) and B3 (business stakeholder). Make sure your team members give their analysis of the report results, but only after B1 has provided you with their STRIDE/DREAD analysis. If you have not heard from B1 yet, use 'NEXT: B1' to suggest talking to B1.",
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
                   system_message="You are a team leader B1. Your team consists of B2 (compliance_officer), B3 (business_stakeholder), and B4 (Threat Modeler). You can talk to the other team leader A1, whose team members are A2 (engineer) and A3 (architect). If you have not heard from A1 yet, use 'NEXT: A1' to suggest talking to A1 and send them the STRIDE/DREAD analysis of the app architecture. When A1 confirms that their team members have provided feedback, you can tell B4 ('NEXT: B4') the analysis is done and to append a new line with TERMINATE to the report.",
                   llm_config=llm_config),
    AssistantAgent(name='B2', 
                   system_message="You are team member B2 (compliance_officer). To cooperate, you tell others whether the identified threats and their mitigation would put the organization at risk of non-compliance. After reviewing the STRIDE and DREAD results of the app architecture, you provide a formalized analysis of the report results which is related to how the threats and mitigations align with compliance standards and regulations. You must start your write-up for the report with 'Compliance Officer Discussion:'.",
                   llm_config=llm_config),
    AssistantAgent(name='B3', 
                   system_message="You are team member B3 (business_stakeholder). To cooperate, you tell others the business context. After reviewing the STRIDE and DREAD results of the app architecture, you provide a formalized analysis of the report results which is related to explaining the critical assets, business impact of potential threats, and which mitigations to prioritize based on business needs. You must start your write-up for the report with 'Business Stakeholder Discussion:'.",
                   llm_config=llm_config),
    AssistantAgent(name='B4', 
                   system_message="You are team member B4. Wait for B1 to confirm the analysis is done, and then append a new line with TERMINATE.",
                   llm_config=llm_config)
]

# Terminates the conversation when TERMINATE is detected.
user_proxy = autogen.UserProxyAgent(
        name="User_proxy",
        system_message="Terminator admin.",
        code_execution_config=False,
        is_termination_msg=is_termination_msg,
        human_input_mode="ALWAYS")

list_of_agents = agents_A + agents_B
list_of_agents.append(user_proxy)

# Create CustomGroupChat
"""
group_chat = CustomGroupChat(
    agents=list_of_agents,  # Include all agents
    messages=['Everyone cooperates and help B4 in their task. Team A has A1, A2 (engineer), A3 (architect). Team B has B1, B2 (compliance officer), and B3 (business stakeholder), and B4. Only members of the same team can talk to one another. Only team leaders (names ending with 1) can talk amongst themselves. You must use "NEXT: B1" to suggest talking to B1 for example; You can suggest only one person, you cannot suggest yourself or the previous speaker. Team leaders can identify the components and attack vectors in the app architecture, and do an analysis of each identified component/vector using STRIDE and DREAD - which they provide to their team.'],
    max_round=11
)
"""
group_chat = autogen.GroupChat(agents=list_of_agents, messages=[], max_round=50)

manager = autogen.GroupChatManager(groupchat=group_chat, llm_config=llm_config)

app_architecture = "Frontend hosted on Vercel, talking to 4 microservices behind an AWS WAF. The microservices are running in containers hosted on AWS AppRunner. The frontend and backend post updates to a mysql database hosted on PlanetScale"
message = "Identify the components and attack vectors in this app architecture, and then get an analysis of each identified component/vector using STRIDE and DREAD. App architecture: " + app_architecture


# Test without FastAPI
sys.stdout = DualOutput('conversation.log')

agents_B[0].initiate_chat(manager, message=message)
sys.stdout.log.close()
sys.stdout = sys.stdout.terminal

