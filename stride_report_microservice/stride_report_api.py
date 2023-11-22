from fastapi import FastAPI, HTTPException, Response, status, Depends, Header
from fastapi.responses import FileResponse
from pydantic import BaseModel
import autogen
from pdf_reports import pug_to_html, write_report
import ast
import os
import sys
import re
import httpx


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


config_list = autogen.config_list_from_json(
    env_or_file="OAI_CONFIG_LIST",
    filter_dict={
        "model": ["gpt-4-1106-preview"],
    },
)


# for local testing
"""
config_list = autogen.config_list_from_json(
    "OAI_CONFIG_LIST",
    file_location="../",
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
    "config_list": config_list,
    "seed": 77,  # change the seed for different trials

}
chatbot = autogen.AssistantAgent(
    name="chatbot",
    system_message="After the thread modeling exercise is complete, add the executive summary, table, and long-form write-up to the report. Only use the functions you have been provided with. Make sure the executive summary starts with 'Executive Summary:'. The summary should identify the top 3 priorities, and be no more than 220 words. The details should be a list of lists of the form '[[component, threat, mitigation], [component, threat, mitigation], ...] . The function will return 'Report generated successfully' if the pdf is successfully created. Reply TERMINATE when the task is done.",
    llm_config=llm_config,
)

# create a UserProxyAgent instance named "user_proxy"
user_proxy = autogen.UserProxyAgent(
    name="user_proxy",
    is_termination_msg=lambda x: x.get("content", "") and x.get("content", "").rstrip().endswith("TERMINATE"),
    human_input_mode="NEVER",
    max_consecutive_auto_reply=5,
    code_execution_config={"work_dir": "coding"},
)


def extract_prompt(text):
    pattern = r"STARTING CONVERSATION:\s*(.*?)\s*DESCRIPTION_END"
    match = re.search(pattern, text, re.DOTALL)

    if match:
        return match.group(1).strip()
    else:
        return "Error printing prompt"

def exec_python(cell, details, longform):

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
      th Component
      th Threats
      th Mitigations
  tbody
      {{ table_rows }}

:markdown
  ## Data Flow Diagram
img(style="width:100%; height:auto;" src="file:///usr/src/app/dfd_diagram.svg")


:markdown
    ##  Discussion
    {{ longform }}

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
    pug_with_discussion = pug_with_table.replace("{{ agent_discussion }}", agent_discussion_pug)


    #print(pug_with_table)

    # Pass the variables to the Pug template
    html = pug_to_html(string=pug_with_discussion, 
                       important_message_body=important_message_body,
                       longform=longform,
                       original_prompt=original_prompt,
                       total_cost=total_cost,
                       total_input=total_input,
                       total_output=total_output,
                       )

    # Generate the report
    write_report(html, "stride_report.pdf")
    return "Report generated successfully"

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

"""
# Test without FastAPI

app_architecture = "The application architecture is a web application with a database. The web application is written in Python and uses the Flask framework. The database is a MySQL database. The web application is hosted on AWS EC2. The web application is a simple blog application that allows users to create posts and comment on posts. The web application uses a MySQL database to store the posts and comments. The web application uses the Flask framework to handle requests and responses. The web application uses the Jinja2 templating engine to render HTML templates. The web application uses the WTForms library to handle forms. The web application uses the Flask-Login library to handle user authentication. The web application uses the Flask-WTF library to handle forms. The web application uses the Flask-Bootstrap library to handle forms. The web application uses the Flask-Admin library to handle forms. The web application uses the Flask-RESTful library to handle forms."
message = "Perform a threat modeling exercise on the app architecture that identifies all app components, STRIDE threats on each component, and mitigations for each STRIDE Threat. App architecture: " + app_architecture + "DESCRIPTION_END"
sys.stdout = DualOutput('conversation.log')
print("STARTING CONVERSATION: ", message)
user_proxy.initiate_chat(
    chatbot,
    message=message
)
sys.stdout.log.close()
sys.stdout = sys.stdout.terminal
"""

# Define your Pydantic model for request validation
class PdfRequest(BaseModel):
    description: str

async def fetch_dfd_diagram(app_architecture: PdfRequest):
    try:
        payload = app_architecture.dict()
        api_key = os.getenv("FASTAPI_KEY")  # Get the API key from environment variable
        dfd_service_url = os.getenv("DFD_SERVICE_URL")  # Get the DFD service URL from environment variable

        headers = {
            "x-api-key": api_key  # Include the API key in the request headers
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            print("Sending request to DFD container")
            response = await client.post(dfd_service_url, json=payload, headers=headers)
            if response.status_code == 200:
                return response.text
            else:
                print("Response Status:", response.status_code)
                print("Response Content:", response.text)
                print("Error in fetch_dfd_diagram:", e)

                raise HTTPException(status_code=500, detail="Error fetching data flow diagram")
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))

def save_svg(svg_content, file_path="dfd_diagram.svg"):
    with open(file_path, "w") as file:
        file.write(svg_content)
    return file_path

def validate_api_key(x_api_key: str = Header(...)):
    print("\n\nValidating API key\n\n")
    expected_api_key = os.getenv("FASTAPI_KEY")  # Get API key from environment variable
    if not expected_api_key or x_api_key != expected_api_key:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return x_api_key


# Create a FastAPI instance
app = FastAPI()

# Other configurations and function definitions remain the same...


@app.post('/generate-stride-report-pdf')
async def generate_pdf(request: PdfRequest, api_key: str = Depends(validate_api_key)):
    try:
        # Fetch and save the SVG diagram
        diagram_request = PdfRequest(description=request.description)
        svg_content = await fetch_dfd_diagram(diagram_request)
        svg_file_path = save_svg(svg_content)

        message = "Perform a threat modeling exercise on the app architecture that identifies all app components, STRIDE threats on each component, and mitigations for each STRIDE Threat. App architecture: " + request.description + "DESCRIPTION_END"

        sys.stdout = DualOutput('conversation.log')
        print("STARTING CONVERSATION: ", message)
        
        # Start the conversation with the user proxy
        user_proxy.initiate_chat(
            chatbot,
            message=message
        )
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



