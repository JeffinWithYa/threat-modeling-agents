import autogen
from autogen.agentchat.groupchat import GroupChat
from autogen.agentchat.agent import Agent
from autogen.agentchat.assistant_agent import AssistantAgent
from pdf_reports import pug_to_html, write_report
import sys
from fastapi import FastAPI, HTTPException, Response, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
"""
config_list = autogen.config_list_from_json(
    env_or_file="OAI_CONFIG_LIST",
    filter_dict={
        "model": ["gpt-4-1106-preview"],
    },
)
"""

original_message = ""

# for local testing

config_list = autogen.config_list_from_json(
    "OAI_CONFIG_LIST",
    file_location="../",
    filter_dict={
        "model": ["gpt-4-1106-preview"],
    },
)

class DualOutput:
    def __init__(self, filename):
        self.terminal = sys.stdout
        self.log = open(filename, "w")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        # This flush method is needed for compatibility with the standard output.
        self.terminal.flush()
        self.log.flush()

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
        # print("\n\nGROUPCHAT MESSAGES", group_chat.messages)
        results = parse_report_details(group_chat.messages)
        #print("\n\nRESULTS", results)
        original_message = group_chat.messages[1]['content'] + "\n\n" + str(group_chat.messages[0])
        exec_python(results, original_message)


        return True
    return False


def generate_pug_table_rows(data):
    pug_rows = []
    pug_rows.append("\n")
    
    for role, messages in data.items():
        # messages are in a list and the last message is most recent
        last_message = messages[-1] if messages else "No feedback"

        # Split the last_message into lines
        message_lines = last_message.split('\n')

        # Start a new row
        pug_row = "    tr\n"

        # Add the role to the row
        pug_row += f"      td {role}\n"

        # Add the message to the row, handling multiple lines
        pug_row += "      td\n"
        for line in message_lines:
            pug_row += f"        | {line}\n"

        pug_rows.append(pug_row)
    
    return "\n".join(pug_rows)

def exec_python(results, prompt):
    agent_discussion = ""
    with open("conversation.log", "r") as f:
        agent_discussion = f.read()
    agent_discussion_pug = '\n    '.join('| ' + line for line in agent_discussion.split('\n'))

    
    original_prompt = prompt
    #print("\n\noriginal prompt\n\n", original_prompt)

    # 'Team A Leader' and 'Team B Leader' are the team leaders
    team_leader_A_last_message = results.get("Team A Leader", [""])[-1]
    team_leader_B_last_message = results.get("Team B Leader", [""])[-1] 

    pug_template_string = """img(style="width:200px; display:block; margin:0 auto; opacity:1;" src="file:///usr/src/app/threat_agents_team.svg")
#sidebar

.ui.stacked.segment.inverted.grey: p.
  This is an auto-generated Threat Modeling Report, assembled by GPT-4 Threat Modeling Agents. 
  The system reviews the specified application architecture. 
  It applies the STRIDE methodology to each component, providing a thorough evaluation of potential security threats, but may still contain errors.
  
.ui.container
  .ui.icon.message.blue.block-center
    i.exclamation.circle.icon
    .content
      .header Executive Summary
      p.
        {{ important_message_body }}


:markdown
    ## Results
table.ui.celled.table
  thead
    tr
      th Role
      th Analysis
  tbody
      {{ table_rows }}

.ui.container
  .ui.icon.message.yellow.block-center
    i.exclamation.circle.icon
    .content
      .header Original Prompt and App Architecture
      p.
        {{ original_prompt }}

:markdown
    ## Appendix
    ### Conversation Log
      {{ agent_discussion }}
    

"""


    # team_members = "Team A: A2 (engineer), A3 (architect). Team B: B2 (compliance officer), B3 (business stakeholder), and B4 (Threat Modeler)."
    important_message_body = """This report outlines the key findings and recommendations from a threat modeling exercise focused on a given application architecture (see appendix), with contributions from two distinct teams.

Team Composition and Perspectives:

Team A: Comprising A2 (Engineer) and A3 (Architect), focused on technical vulnerabilities and architectural improvements.
Team B: Including B2 (Compliance Officer), B3 (Business Stakeholder), and B4 (Threat Modeler), emphasizing compliance, business impact, and holistic threat modeling. 

Key outcomes of the exercise include:

Identification of Critical Threats: The team pinpoints several high-priority threats that could significantly impact the application's security. These include risks related to data breaches, unauthorized access, and system downtimes.

Mitigation Strategies: For each identified threat, the team proposes tailored mitigation strategies. These range from immediate short-term fixes to long-term structural changes in the application's architecture.

Prioritization of Actions: The team has collectively prioritized the proposed actions based on the severity of threats and the feasibility of implementing solutions. This prioritization aims to optimize resource allocation and ensure a rapid response to the most critical issues.

"""
    table_rows = generate_pug_table_rows(results)
    #print("\n\ntable rows\n\n", table_rows)

    #print("\n\n Agent discussion\n\n", agent_discussion)
    pug_with_table = pug_template_string.replace("{{ table_rows }}", table_rows)
    pug_with_discussion = pug_with_table.replace("{{ agent_discussion }}", agent_discussion_pug)



    print("\n\npug with table\n\n", pug_with_discussion)

    html = pug_to_html(string=pug_with_discussion, 
                       important_message_body=important_message_body,
                       original_prompt=original_prompt)

    # Generate the report
    write_report(html, "stakeholder_report.pdf")
    return "Report generated successfully"


def parse_report_details(messages):
    stakeholders = {
    "A1": "Team A Leader",
    "A2": "Engineering",
    "A3": "Architecture",
    "B1": "Team B Leader",
    "B2": "Compliance Officer",
    "B3": "Business Stakeholder",
    "B4": "Threat Modeler",
    "User_proxy": "Human User"
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

    #print("PUG table results", results)
    return results
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
        human_input_mode="NEVER")

list_of_agents = agents_A + agents_B
list_of_agents.append(user_proxy)

# Create CustomGroupChat
group_chat = CustomGroupChat(
    agents=list_of_agents,  # Include all agents
    messages=['Everyone cooperates and help B4 in their task. Team A has A1, A2 (engineer), A3 (architect). Team B has B1, B2 (compliance officer), and B3 (business stakeholder), and B4. Only members of the same team can talk to one another. Only team leaders (names ending with 1) can talk amongst themselves. You must use "NEXT: B1" to suggest talking to B1 for example; You can suggest only one person, you cannot suggest yourself or the previous speaker. Team leaders can identify the components and attack vectors in the app architecture, and do an analysis of each identified component/vector using STRIDE and DREAD - which they provide to their team.'],
    max_round=30
)


# Create the manager
llm_config = {"config_list": config_list, "seed": 28}  # cache_seed is None because we want to observe if there is any communication pattern difference if we reran the group chat.

manager = autogen.GroupChatManager(groupchat=group_chat, llm_config=llm_config)

app_architecture = "The application architecture is a web application with a database. The web application is written in Python and uses the Flask framework. The database is a MySQL database. The web application is hosted on AWS EC2. The web application is a simple blog application that allows users to create posts and comment on posts. The web application uses a MySQL database to store the posts and comments. The web application uses the Flask framework to handle requests and responses. The web application uses the Jinja2 templating engine to render HTML templates. The web application uses the WTForms library to handle forms. The web application uses the Flask-Login library to handle user authentication. The web application uses the Flask-WTF library to handle forms. The web application uses the Flask-Bootstrap library to handle forms. The web application uses the Flask-Admin library to handle forms. The web application uses the Flask-RESTful library to handle forms."
message = "Identify the components and attack vectors in this app architecture, and then get an analysis of each identified component/vector using STRIDE and DREAD. App architecture: " + app_architecture

# Test without FastAPI
# """"
sys.stdout = DualOutput('conversation.log')
agents_B[0].initiate_chat(manager, message=message)
sys.stdout.log.close()
sys.stdout = sys.stdout.terminal
# """"


""""
# Define your Pydantic model for request validation
class PdfRequest(BaseModel):
    description: str

# Create a FastAPI instance
app = FastAPI()

# Other configurations and function definitions remain the same...

@app.get('/')
def hello():
    return {"message": "Hello World!"}

@app.post('/generate-roles-report-pdf')
async def generate_diagram(request: PdfRequest):
    try:
        message = "Identify the components and attack vectors in this app architecture, and then get an analysis of each identified component/vector using STRIDE and DREAD. App architecture: " + request.description
        original_message = message

        # Start the conversation with the user proxy
        sys.stdout = DualOutput('conversation.log')
        agents_B[0].initiate_chat(manager, message=message)
        sys.stdout.log.close()
        sys.stdout = sys.stdout.terminal

        pdf_path = 'stride_report.pdf'

        if os.path.exists(pdf_path):
            return FileResponse(pdf_path, media_type='application/pdf')
        else:
            raise HTTPException(status_code=404, detail="File not found")

    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))

""""