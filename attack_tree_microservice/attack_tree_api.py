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

# for local testing (no environment variables)
"""
config_list = autogen.config_list_from_json(
    "OAI_CONFIG_LIST",
    file_location="../",
    filter_dict={
        "model": ["gpt-4-1106-preview"],
    },
)
"""

# for deployment (environment variables)
# """
config_list = autogen.config_list_from_json(
    env_or_file="OAI_CONFIG_LIST",
    filter_dict={
        "model": ["gpt-4-1106-preview"],
    },
)
# """

llm_config = {
    "functions": [
        {
            "name": "python",
            "description": "Writes the graphviz script to a file that creates attack tree diagram.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cell": {
                        "type": "string",
                        "description": "The text containing the graphviz script.",
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
    system_message="""Using only the functions available to you, you create attack tree diagrams by writing a script to a file and outputting the data flow diagram. Make sure you call the render function with 'attack_tree' and specify 'svg' for format. Make sure the margin and pad are 0 (specified in dot.attr() function). Here is an example script that you should base your output off of: 
    # filename: attack_tree.py

from graphviz import Digraph

# Create a directed graph
dot = Digraph(comment='Attack Tree')
dot.attr('graph', margin='0', pad='0')


# Add nodes for each potential attack vector
dot.node('A', 'Stealing User\'s Data', color='red')
dot.node('B', 'Amazon Cognito', color='lightblue')
dot.node('C', 'Amazon S3', color='lightblue')
dot.node('D', 'DynamoDB', color='lightblue')
dot.node('E', 'AWS Lambda', color='lightblue')
dot.node('F', 'GameLift', color='lightblue')
dot.node('G', 'AppSync', color='lightblue')
dot.node('H', 'AWS Analytics', color='lightblue')
dot.node('I', 'Amazon Pinpoint', color='lightblue')

# Add edges to represent the attack vectors
dot.edge('A', 'B', label='Intercept login/registration data')
dot.edge('A', 'C', label='Intercept game assets')
dot.edge('A', 'D', label='Manipulate game state data')
dot.edge('A', 'E', label='Exploit Lambda functions')
dot.edge('A', 'F', label='Attack multiplayer events')
dot.edge('A', 'G', label='Intercept offline plays data')
dot.edge('A', 'H', label='Access user behavior data')
dot.edge('A', 'I', label='Send malicious notifications')

# Save the graph as a SVG file
dot.format = 'svg'
dot.render('attack_tree', view=False)

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
def extract_prompt(text):
    pattern = r"STARTING CONVERSATION:\s*(.*?)\s*DESCRIPTION_END"
    match = re.search(pattern, text, re.DOTALL)

    if match:
        return match.group(1).strip()
    else:
        return "Error printing prompt"

def exec_python(cell):
    
    pytm_template = """
{}
    """
    with open('attack_tree_out.py', 'w') as file:
        formatted_template = pytm_template.format(cell)
        with open("attack_tree_out.py", 'w') as file:
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
  This is an auto-generated Attack Tree, assembled by GPT-4 Threat Modeling Agents. 
  The system reviews the specified application architecture and specified attack (top node of tree), and generates an attack tree diagram using GraphViz. The result may still contain errors.
  
img(style="width:600px; height:600px; display:block; margin:0 auto; opacity:1;" src="file:///usr/src/app/attack_tree.svg")

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
    write_report(html, "attack_tree.pdf")
    return "Report generated successfully"

def exec_sh(script):
    # The command you want to execute
    command = "python3 attack_tree_out.py"
    
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

"""
# Test without FastAPI
topnode = "Stealing User's Data"
app_architecture = "In a web application hosted on AWS, the data flow begins with the user's interaction with the front-end, which triggers an HTTP request. This request is routed through Amazon Route 53 to an Elastic Load Balancer, which then directs the traffic to the appropriate EC2 instances where the application is hosted. The application code, running on an AWS Elastic Beanstalk environment, processes the request, which includes querying an Amazon RDS database and Amazon DynamoDB table to retrieve or store data. AWS Lambda functions are also utilized for serverless computation. The application interacts with additional AWS services like S3 for object storage, and Amazon ElastiCache to access frequently requested data quickly. Once the server-side processing is complete, the data is formatted (as JSON) and sent back through the Internet to the user's browser, where it is rendered, and any dynamic client-side actions are handled by JavaScript."
message = "Create an attack tree diagram for the following app architecture, " + "with the top node being " + topnode + ". App architecture: " + app_architecture

# Start the conversation with the user proxy
sys.stdout = DualOutput('conversation.log')
print("STARTING CONVERSATION: ", message)
user_proxy.initiate_chat(
    chatbot,
    message=message
)
sys.stdout.log.close()
sys.stdout = sys.stdout.terminal
"""


# Define Pydantic model for request validation
class DiagramRequest(BaseModel):
    description: str
    topnode: str

# Create a FastAPI instance
app = FastAPI()

# Other configurations and function definitions remain the same...

@app.get('/')
def hello():
    return {"message": "Hello World!"}

@app.post('/generate-diagram')
async def generate_diagram(request: DiagramRequest):
    try:
        message = "Create an attack tree diagram for the following app architecture, " + "with the top node being " + request.topnode + ". App architecture: " + request.description + "DESCRIPTION_END"

        # Start the conversation with the user proxy
        user_proxy.initiate_chat(
            chatbot,
            message=message
        )

        image_path = 'attack_tree.svg'

        if os.path.exists(image_path):
            return FileResponse(image_path, media_type='image/svg')
        else:
            raise HTTPException(status_code=404, detail="Image not found")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/generate-diagram-pdf')
async def generate_diagram(request: DiagramRequest):
    try:
        message = "Create an attack tree diagram for the following app architecture, " + "with the top node being " + request.topnode + ". App architecture: " + request.description + "DESCRIPTION_END"

        # Start the conversation with the user proxy
        sys.stdout = DualOutput('conversation.log')
        print("STARTING CONVERSATION: ", message)
        user_proxy.initiate_chat(
            chatbot,
            message=message
        )
        sys.stdout.log.close()
        sys.stdout = sys.stdout.terminal

        result_path = 'attack_tree.pdf'

        if os.path.exists(result_path):
            return FileResponse(result_path, media_type='application/pdf')
        else:
            raise HTTPException(status_code=404, detail="File not found")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

