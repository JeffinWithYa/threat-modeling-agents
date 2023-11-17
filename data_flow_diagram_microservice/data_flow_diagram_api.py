from fastapi import FastAPI, HTTPException, Response, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import subprocess
import autogen
import sys
import re
from pdf_reports import pug_to_html, write_report

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

def calculate_cost(conversation_log):
    conversation_log = conversation_log[1:]
    input_cost_per_1000 = 0.01
    output_cost_per_1000 = 0.03

    total_input_tokens = 0
    total_output_tokens = 0
    total_characters = 0

    for log in conversation_log:
        content = str(log)
        total_characters += len(content)
        total_input_tokens += len(content) // 4
        total_output_tokens = total_characters // 4

    total_input = (total_input_tokens * input_cost_per_1000)/1000
    total_output = (total_output_tokens * output_cost_per_1000)/1000
    total_cost = (total_input_tokens * input_cost_per_1000 / 1000) + (total_output_tokens * output_cost_per_1000 / 1000)
    return total_cost, total_input, total_output

# define functions according to the function desription
def extract_prompt(text):
    pattern = r"STARTING CONVERSATION:\s*(.*?)\s*DESCRIPTION_END"
    match = re.search(pattern, text, re.DOTALL)

    if match:
        return match.group(1).strip()
    else:
        return "Error printing prompt"

config_list = autogen.config_list_from_json(
    env_or_file="OAI_CONFIG_LIST",
    filter_dict={
        "model": ["gpt-4-1106-preview"],
    },
)
llm_config = {
    "functions": [
        {
            "name": "python",
            "description": "Writes the pytm script to a file and creates data flow diagram.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cell": {
                        "type": "string",
                        "description": "The text containing the pytm script.",
                    },
                },
                "required": ["cell"],
            },
            
        },
    ],
    "config_list": config_list,
    "seed": 79,  # change the seed for different trials

}
chatbot = autogen.AssistantAgent(
    name="chatbot",
    system_message="""Using only the functions available to you, you create data flow diagrams by writing a pytm script to a file and outputting the data flow diagram. The pytm script is being injected into a template, so do not write any imports, with statements, or a main function. Here is an example pytm script that you should base your output off of. Note that it first defines the app components, and then how data flows between them. You should only pass 3 arguments to DataFlow().: 
    tm = TM("Game App Data Flow")
tm.description = "Threat model for an application architecture with various services."
tm.isOrdered = True
tm.mergeResponses = True

internet = Boundary("Internet")

aws_cloud = Boundary("AWS Cloud")

user = Actor("User")
user.inBoundary = internet

cognito = ExternalEntity("Amazon Cognito")
cognito.inBoundary = aws_cloud

s3 = Datastore("Amazon S3")
s3.inBoundary = aws_cloud

gamelift = ExternalEntity("Amazon GameLift")
gamelift.inBoundary = aws_cloud

appsync = Process("AWS AppSync")
appsync.inBoundary = aws_cloud

analytics = Process("AWS Analytics")
analytics.inBoundary = aws_cloud

pinpoint = ExternalEntity("Amazon Pinpoint")
pinpoint.inBoundary = aws_cloud

# Data definitions
game_assets = Data("Game Assets")
game_state = Data("Game State")

# Dataflows
user_to_cognito = Dataflow(user, cognito, "User Authentication")
user_to_s3 = Dataflow(user, s3, "Fetch Game Assets")

Reply 'TERMINATE' when done.    
    """,
    llm_config=llm_config,
)

# create a UserProxyAgent instance named "user_proxy"
user_proxy = autogen.UserProxyAgent(
    name="user_proxy",
    is_termination_msg=lambda x: x.get("content", "") and x.get("content", "").rstrip().endswith("TERMINATE"),
    human_input_mode="NEVER",
    max_consecutive_auto_reply=10,
    code_execution_config={"work_dir": "coding"},
)

# define functions according to the function desription

def exec_python(cell):
    
    pytm_template = """
#!/usr/bin/env python
from pytm import (
    TM,
    Actor,
    Boundary,
    Classification,
    Data,
    Dataflow,
    Datastore,
    Lambda,
    Server,
    ExternalEntity,
    Process,
    DatastoreType,
)

{}

if __name__ == "__main__":
    tm.process()
    """
    with open('pytm_script.py', 'w') as file:
        formatted_template = pytm_template.format(cell)
        with open("pytm_script.py", 'w') as file:
            file.write(formatted_template)

    print("pytm File written successfully")
    exec_sh("sh")

        # Create PDF
    agent_discussion = ""
    total_cost = 0
    total_input = 0
    total_output = 0
    original_prompt = ""
    with open("conversation.log", "r") as f:
        agent_discussion = f.read()
        total_cost, total_input, total_output = calculate_cost(agent_discussion)
        original_prompt = extract_prompt(agent_discussion)

    agent_discussion_pug = '\n    '.join('| ' + line for line in agent_discussion.split('\n'))

    pug_template_string = """img(style="width:200px; display:block; margin:0 auto; opacity:1;" src="file:///usr/src/app/threat_agents_team.svg")
#sidebar

.ui.stacked.segment.inverted.grey: p.
  This is an auto-generated Data Flow Diagram, assembled by GPT-4 Threat Modeling Agents. 
  The system reviews the specified application architecture, and generates a data flow diagram using pytm and GraphViz. The result may still contain errors.
  
img(style="width:600px; height:600px; display:block; margin:0 auto; opacity:1;" src="file:///usr/src/app/tm/dfd.svg")

:markdown
    ## Appendix

.ui.container
  .ui.icon.message.yellow.block-center
    i.exclamation.circle.icon
    .content
      .header Original Prompt and Inputted App Architecture
      p.
        {{ original_prompt }}

:markdown
    ### Usage Costs
        #### Total Cost: ${{ total_cost }} USD
        #### Input Tokens Cost: ${{ total_input }} USD
        #### Output Tokens Cost: ${{ total_output }} USD
    ### Conversation Log
      {{ agent_discussion }}
      """
    pug_with_discussion = pug_template_string.replace("{{ agent_discussion }}", agent_discussion_pug)
    # Pass the variables to the Pug template
    html = pug_to_html(string=pug_with_discussion, 
                       original_prompt=original_prompt,
                       total_cost=total_cost,
                       total_input=total_input,
                       total_output=total_output,
                       )

    # Generate the report
    write_report(html, "dfd_report.pdf")
    return "Report generated successfully"
    


def exec_sh(script):
    # The command you want to execute
    command = "python3 pytm_script.py --dfd | dot -Tsvg -o tm/dfd.svg"
    
    # Execute the command
    process = subprocess.Popen(
        command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    # Wait for the command to complete
    stdout, stderr = process.communicate()

    # Check if the command was successful
    if process.returncode == 0:
        print("Command executed successfully.")
        #print(stdout.decode())
    else:
        print("An error occurred while executing the command.")
        #print(stderr.decode())

# register the functions
user_proxy.register_function(
    function_map={
        "python": exec_python        }
)
# Define your Pydantic model for request validation
class DiagramRequest(BaseModel):
    description: str

# Create a FastAPI instance
app = FastAPI()

# Other configurations and function definitions remain the same...

@app.get('/')
def hello():
    return {"message": "Hello World!"}

@app.post('/generate-diagram')
async def generate_diagram(request: DiagramRequest):
    try:
        message = "Create a data flow diagram for the following app architecture: " + request.description + "DESCRIPTION_END"

        # Start the conversation with the user proxy
        sys.stdout = DualOutput('conversation.log')
        print("STARTING CONVERSATION: ", message)


        user_proxy.initiate_chat(
            chatbot,
            message=message
        )
        sys.stdout.log.close()
        sys.stdout = sys.stdout.terminal

        image_path = 'tm/dfd.svg'

        if os.path.exists(image_path):
            return FileResponse(image_path, media_type='image/svg')
        else:
            raise HTTPException(status_code=404, detail="Image not found")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/generate-diagram-pdf')
async def generate_diagram(request: DiagramRequest):
    try:
        message = "Create a data flow diagram for the following app architecture: " + request.description + "DESCRIPTION_END"

        # Start the conversation with the user proxy
        sys.stdout = DualOutput('conversation.log')
        print("STARTING CONVERSATION: ", message)

        user_proxy.initiate_chat(
            chatbot,
            message=message
        )
        sys.stdout.log.close()
        sys.stdout = sys.stdout.terminal

        result_path = 'dfd_report.pdf'

        if os.path.exists(result_path):
            return FileResponse(result_path, media_type='application/pdf')
        else:
            raise HTTPException(status_code=404, detail="File not found")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
# No need to specify host and port here, run with Uvicorn or similar ASGI server
