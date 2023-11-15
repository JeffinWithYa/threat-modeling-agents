from fastapi import FastAPI, HTTPException, Response, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
import autogen
from pdf_reports import pug_to_html, write_report
import ast
import os

from autogen.agentchat.groupchat import GroupChat
from autogen.agentchat.agent import Agent
from autogen.agentchat.assistant_agent import AssistantAgent
import random
from typing import List, Dict

config_list = autogen.config_list_from_json(
    "OAI_CONFIG_LIST",
    file_location="../",
    filter_dict={
        "model": ["gpt-4-1106-preview"],
    },
)

llm_config_no_code = {"config_list": config_list}  # cache_seed is None because we want to observe if there is any communication pattern difference if we reran the group chat.


"""
config_list = autogen.config_list_from_json(
    env_or_file="OAI_CONFIG_LIST",
    filter_dict={
        "model": ["gpt-4-1106-preview"],
    },
)
"""

llm_config = {
    "functions": [
        {
            "name": "python",
            "description": "Adds the executive summary, details, and longform to the report.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cell": {
                        "type": "string",
                        "description": "An executive summary of the threat modeling exercise.",
                    },
                    "details": {
                        "type": "string",
                        "description": "Details of the threat modeling exercise.",
                    },
                    "longform": {
                        "type": "string",
                        "description": "Longform write-up of the threat modeling exercise.",
                    },
                },
                "required": ["cell", "details", "longform"],
            },
        },
    ],
    "config_list": config_list
}

class CustomGroupChat(GroupChat):
    def __init__(self, agents, messages, max_round=22):
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
                    return self.agent_by_name('reporter')
                except ValueError:
                    pass  # If 'reporter' is not a valid name, continue with normal selection
        
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
agents_technical = [
    AssistantAgent(name='technical1', 
                   system_message="You are a team leader technical1, your team consists of the engineer, architect. You can talk to the other team leader business1, whose team members are compliance_officer and business_stakeholder. Do not use function calls.",
                   llm_config=llm_config),
    AssistantAgent(name='technical_engineer', 
                   system_message="You are team member engineer. To cooperate, you tell others the potential coding pitfalls in the app architecture that might lead to vulnerabilities and suggest possible solutions. Your discussion is related to implementation details and providing mitigation strategies based on coding best practices. Do not use function calls.",
                   llm_config=llm_config),
    AssistantAgent(name='technical_architect', 
                   system_message="You are team member architect. To cooperate, you tell others the potential weak points in the app architecture where threats may be exploited. Using your knowledge, you help identify potential weak points in the system and propose architectural changes to mitigate threats. Do not use function calls.",
                   llm_config=llm_config)
]

agents_business = [
    AssistantAgent(name='business1', 
                   system_message="You are a team leader business1. Your team consists of compliance_officer, business_stakeholder, and facilitator. You can talk to the other team leader technical1, whose team members are engineer and architect. Use NEXT: A1 to suggest talking to technical1. Do not use function calls.",
                   llm_config=llm_config),
    AssistantAgent(name='business_compliance_officer', 
                   system_message="You are team member compliance_officer. To cooperate, you tell others whether the identified threats and their mitigation would put the organization at risk of non-compliance. Your discussion relates to how threat modeling and subsequent mitigations align with compliance standards and regulations Do not use function calls.",
                   llm_config=llm_config),
    AssistantAgent(name='business_stakeholder', 
                   system_message="You are team member business_stakeholder. To cooperate, you tell others the the business context. You explain the critical assets, business impacts of potential threats, and help prioritize mitigation based on business needs. You share the potential business implications of identified threats and discuss how to align security priorities with business objectives. Do not use function calls.",
                   llm_config=llm_config),
    AssistantAgent(name='business_facilitator', 
                   system_message="You are the facilitator. Your job is to put together a threat modeling report based on feedback from the technical team and business team. Once you have the input from everyone, you provide a 220 word executive summary (highest priority items) and the team's feedback to the reporter. Do not use function calls.",
                   llm_config=llm_config)
]

# Terminates the conversation when TERMINATE is detected.
user_proxy = autogen.UserProxyAgent(
        name="reporter",
        system_message="You are the reporter. Your job is to generate the threat modeling report pdf based on feedback from the facilitator. Once you have the input, write the report by only calling the functions you have available to you. Make sure the executive summary starts with 'Executive Summary:'. The summary should identify the top 3 priorities, and be no more than 220 words. The details should be a list of lists of the form '[[team member name, their feedback, key points from their feedback], [team member name, their feedback, key points from their feedback], ...] . The function will return 'Report generated successfully' if the pdf is successfully created. Reply TERMINATE when the task is done.",
        is_termination_msg=is_termination_msg,
        code_execution_config={"work_dir": "coding"},
        human_input_mode="NEVER",
        ),
        

list_of_agents = agents_technical + agents_business
list_of_agents.append(user_proxy)

# Create CustomGroupChat
group_chat = CustomGroupChat(
    agents=list_of_agents,  # Include all agents
    messages=['Everyone cooperate and help facilitator in their task. Only the reporter should make function calls. Team Technical has technical1, engineer, architect. Team Business has business1, compliance_officer, and business_stakeholer. Only members of the same team can talk to one another. Only team leaders (names ending with 1) can talk amongst themselves. Reporter can talk to facilitator. You must use "NEXT: business1" to suggest talking to business1 for example; You can suggest only one person, you cannot suggest yourself or the previous speaker; You can also dont suggest anyone.'],
    max_round=30
)


# Create the manager
#llm_config = {"config_list": config_list}  # cache_seed is None because we want to observe if there is any communication pattern difference if we reran the group chat.
manager = autogen.GroupChatManager(groupchat=group_chat, llm_config=llm_config)

# define functions according to the function desription

def exec_python(cell, details, longform):

    pug_template_string = """img(style="width:200px; display:block; margin:0 auto; opacity:1;" src="file:///Users/jeffreyjeyachandren/Desktop/threat-modeling-agents/threat-modeling-agents/tm_with_roles_microservice/threat_agents_team.svg")
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
  ##  Results
table.ui.celled.table
  thead
    tr
      th Team Member
      th Feedback
      th Key Takeaways
  tbody
      {{ table_rows }}

:markdown
    ##  Discussion
    {{ longform }}
      
      """


    #print("/n/n details: ", details)

    # Strip quotes from the beginning and end of the string
    s = cell.strip('"\'')
    while s.startswith('#'):
        s = s[1:].strip()
    
    # Check if the string starts with 'Executive Summary' and remove it
    exec_summ_prefix = 'Executive Summary:'
    if s.startswith(exec_summ_prefix):
        # Slice the string to remove the 'Executive Summary' part
        s = s[len(exec_summ_prefix):].strip()

    important_message_body = s
    table_rows = generate_pug_table_rows(details)
    pug_with_table = pug_template_string.replace("{{ table_rows }}", table_rows)

    #print(pug_with_table)

    # Pass the variables to the Pug template
    html = pug_to_html(string=pug_with_table, 
                       important_message_body=important_message_body,
                       longform=longform,
                       )

    # Generate the report
    write_report(html, "stride_report.pdf")

def generate_pug_table_rows(data):
    pug_rows = []
    data_list = ast.literal_eval(data)

    for row in data_list:
        #print("\n\nrow: ", row)
        # Start a new row
        pug_row = "  tr\n"
        
        # Add each cell in the row
        for cell in row:
            #print("\nitem in row: ", cell)
            pug_row += f"  td {cell}\n"
        
        pug_rows.append(pug_row)
    
    return "\n".join(pug_rows)

def exec_sh(script):
    return user_proxy.execute_code_blocks([("sh", script)])

# register the functions
user_proxy.register_function(
    function_map={
        "python": exec_python    
        }
)

app_architecture = "The application architecture is a web application with a database. The web application is written in Python and uses the Flask framework. The database is a MySQL database. The web application is hosted on AWS EC2. The web application is a simple blog application that allows users to create posts and comment on posts. The web application uses a MySQL database to store the posts and comments. The web application uses the Flask framework to handle requests and responses. The web application uses the Jinja2 templating engine to render HTML templates. The web application uses the WTForms library to handle forms. The web application uses the Flask-Login library to handle user authentication. The web application uses the Flask-WTF library to handle forms. The web application uses the Flask-Bootstrap library to handle forms. The web application uses the Flask-Admin library to handle forms. The web application uses the Flask-RESTful library to handle forms."
message = "Create a threat modeling report on this app architecture that includes feedback from the engineer, architect, business stakeholder, and compliance officer. App architecture: " + app_architecture

agents_business[3].initiate_chat(manager, message=message)


# FastAPI
"""
# Define your Pydantic model for request validation
class PdfRequest(BaseModel):
    description: str

# Create a FastAPI instance
app = FastAPI()

# Other configurations and function definitions remain the same...

@app.get('/')
def hello():
    return {"message": "Hello World!"}


@app.post('/generate-stakeholder-report-pdf')
async def generate_diagram(request: PdfRequest):
    try:
        message = "Create a threat modeling report on this app architecture that includes feedback from the engineer, architect, business stakeholder, and compliance officer. App architecture: " + request.description


        # Initiates the chat with B2
        agents_business[3].initiate_chat(manager, message=message)

        pdf_path = 'stride_report.pdf'

        if os.path.exists(pdf_path):
            return FileResponse(pdf_path, media_type='application/pdf')
        else:
            raise HTTPException(status_code=404, detail="File not found")

    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))

"""
