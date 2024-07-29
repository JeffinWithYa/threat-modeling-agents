from fastapi import FastAPI, HTTPException, Response, status, Depends, Header, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
import autogen
from pdf_reports import pug_to_html, write_report
import ast
import os
import sys
import re
from databases import Database
import ssl
import uuid
from concurrent.futures import ThreadPoolExecutor
import asyncio
import requests
executor = ThreadPoolExecutor(max_workers=4)  # Adjust based on your needs
from typing import Any, Dict, List, Optional, Union



DATABASE_URL = os.getenv("DATABASE_URL") 
ssl_context = ssl.create_default_context(cafile='/etc/ssl/certs/ca-certificates.crt')
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_REQUIRED

database = Database(DATABASE_URL, ssl=ssl_context)


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
                    "task_id": {
                        "type": "string",
                        "description": "Task ID of the task to be updated.",
                    }
                },
                "required": ["cell", "details", "longform", "task_id"],
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

def exec_python(cell, details, longform, task_id):

    agent_discussion = ""
    total_cost = 0
    total_input = 0
    total_output = 0
    original_prompt = ""

    log_file = log_file = "conversation_" + task_id + ".log"
    with open(log_file, "r") as f:
        agent_discussion = f.read()
        total_cost, total_input, total_output = calculate_cost(agent_discussion)
        original_prompt = extract_prompt(agent_discussion)




    agent_discussion_pug = '\n    '.join('| ' + line for line in agent_discussion.split('\n'))


    pug_template_string = """img(style="width:200px; display:block; margin:0 auto; opacity:1;" src="file:///usr/src/app/threat_agents_team.svg")
#sidebar

.ui.stacked.segment.inverted.grey: p.
  Threat Modeling Report
  
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
img(style="width:100%; height:auto;" src="file:///usr/src/app/{{ image_path }}")


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
    pug_with_discussion = pug_with_table.replace("{{ agent_discussion }}", agent_discussion_pug)
    image_path = "dfd_" + task_id + ".svg"
    print("\n\nIMAGE PATH: ", image_path)


    #print(pug_with_table)

    # Pass the variables to the Pug template
    html = pug_to_html(string=pug_with_discussion, 
                       important_message_body=important_message_body,
                       longform=longform,
                       original_prompt=original_prompt,
                       total_cost=total_cost,
                       total_input=total_input,
                       total_output=total_output,
                       image_path=image_path
                       )

    # Generate the report
    final_report = "stride_report_" + task_id + ".pdf" 
    write_report(html, final_report)
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

def initiate_chat_blocking(task_id: str, request_description: str):
    message = "Perform a threat modeling exercise on the app architecture that identifies all app components, STRIDE threats on each component, and mitigations for each STRIDE Threat. App architecture: " + request_description + "DESCRIPTION_END" + ". When calling functions, use task_id: " + task_id + " as the second argument."

    # Start the conversation with the user proxy
    sys.stdout = DualOutput(f'conversation_{task_id}.log')
    print("STARTING CONVERSATION: ", message)

    user_proxy.initiate_chat(
        chatbot,
        message=message
    )
    sys.stdout.log.close()
    sys.stdout = sys.stdout.terminal



def fetch_dfd_diagram(app_architecture: PdfRequest):
    try:
        payload = app_architecture.dict()
        api_key = os.getenv("FASTAPI_KEY")  # Get the API key from environment variable
        dfd_service_url = os.getenv("DFD_API_URL")  # Get the DFD service URL from environment variable

        headers = {
            "x-api-key": api_key  # Include the API key in the request headers
        }

        response = requests.post(dfd_service_url, json=payload, headers=headers, timeout=180.0)
        if response.status_code == 200:
            return response.text
        else:
            #print("Response Status:", response.status_code)
            #print("Response Content:", response.text)
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

async def generate_pdf_background(task_id: str, request_description: str):
    try:
        loop = asyncio.get_event_loop()

        diagram_request = PdfRequest(description=request_description)
        svg_content = await loop.run_in_executor(executor, fetch_dfd_diagram, diagram_request)
        print("\n\nBACK FROM FETCHING DFD DIAGRAM")
        svg_file_name = "dfd_" + task_id + ".svg"
        svg_file_path = save_svg(svg_content, svg_file_name)
        
        await loop.run_in_executor(executor, initiate_chat_blocking, task_id, request_description)
        
        pdf_path = f"stride_report_{task_id}.pdf"
        print("\n\nPDF PATH: ", pdf_path)

        # Update the task status to completed and set the file path in the database
        await database.execute("UPDATE TaskStatus SET status = :status, filePath = :filePath, updatedAt = NOW() WHERE id = :id", {"id": task_id, "status": "completed", "filePath": pdf_path})


    except Exception as e:
        print("\n\n PDF CREATION FAILED", e)
        # Update the task status to failed in the database
        await database.execute("UPDATE TaskStatus SET status = :status, updatedAt = NOW() WHERE id = :id", {"id": task_id, "status": "failed"})

def is_desired_format(message):
    return re.search(r'.* \(to .*\):', message) is not None
# Create a FastAPI instance
app = FastAPI()

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

# Other configurations and function definitions remain the same...


@app.post('/generate-stride-report-direct')
async def generate_pdf(request: PdfRequest, api_key: str = Depends(validate_api_key)):
    try:
        task_id = str(uuid.uuid4())
        print("\n\nCALLING DB WITH ", task_id)
        await database.execute("INSERT INTO TaskStatus (id, status, createdAt, updatedAt) VALUES (:id, :status, NOW(), NOW())", {"id": task_id, "status": "pending"})
        print("\n\nDB CALL COMPLETE")
        # Fetch and save the SVG diagram
        diagram_request = PdfRequest(description=request.description)
        svg_content = await fetch_dfd_diagram(diagram_request)
        svg_file_name = "dfd_" + task_id + ".svg"
        svg_file_path = save_svg(svg_content, svg_file_name)

        message = "Perform a threat modeling exercise on the app architecture that identifies all app components, STRIDE threats on each component, and mitigations for each STRIDE Threat. App architecture: " + request.description + "DESCRIPTION_END" + ". When calling functions, use task_id: " + task_id + " as the second argument."

        sys.stdout = DualOutput(f'conversation_{task_id}.log')
        print("STARTING CONVERSATION: ", message)
        
        # Start the conversation with the user proxy
        user_proxy.initiate_chat(
            chatbot,
            message=message
        )
        sys.stdout.log.close()
        sys.stdout = sys.stdout.terminal

        pdf_path = f"stride_report_{task_id}.pdf"

        await database.execute("UPDATE TaskStatus SET status = :status, filePath = :filePath, updatedAt = NOW() WHERE id = :id", {"id": task_id, "status": "completed", "filePath": pdf_path})

        if os.path.exists(pdf_path):
            return FileResponse(pdf_path, media_type='application/pdf')
        else:
            raise HTTPException(status_code=404, detail="File not found")

    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/generate-stride-report')
async def generate_stride(request: PdfRequest, background_tasks: BackgroundTasks, api_key: str = Depends(validate_api_key)):
    task_id = str(uuid.uuid4())
    await database.execute("INSERT INTO TaskStatus (id, status, createdAt, updatedAt) VALUES (:id, :status, NOW(), NOW())", {"id": task_id, "status": "pending"})
    print("Request description: ", request.description)
    background_tasks.add_task(generate_pdf_background, task_id, request.description)
    return {"task_id": task_id}

@app.get("/get-stride/{task_id}")
async def get_stride(task_id: str, api_key: str = Depends(validate_api_key)):
    query = "SELECT status, filePath FROM TaskStatus WHERE id = :task_id"
    result = await database.fetch_one(query, {"task_id": task_id})

    if result is None:
        raise HTTPException(status_code=404, detail="Task not found")

    task_status, pdf_path = result['status'], result['filePath']

    if task_status == "completed":
        attempts = 0
        max_attempts = 5
        delay_seconds = 2
        while not os.path.exists(pdf_path) and attempts < max_attempts:
            await asyncio.sleep(delay_seconds)
            attempts += 1
        
        if os.path.exists(pdf_path):
            return FileResponse(pdf_path, media_type='application/pdf')
        else:
            raise HTTPException(status_code=404, detail="File not found or task failed")
    elif task_status == "pending":
        raise HTTPException(status_code=202, detail="Task is still processing")
    else:
        raise HTTPException(status_code=404, detail="PDF not found or task failed")

@app.get("/convo/{task_id}")
async def get_last_message(task_id: str, api_key: str = Depends(validate_api_key)):
    # Construct the file path for the conversation log
    log_file_path = f"conversation_{task_id}.log"
    print("INFO: LOG PATH in CONVO API: ", log_file_path)

    
    # Check if the log file exists
    if not os.path.exists(log_file_path):
        raise HTTPException(status_code=404, detail="Log file not found")

    try:
        # Open the log file and read the contents
        with open(log_file_path, "r") as file:
            conversation_log = file.read()
        
        # Check if the log is empty
        if not conversation_log:
            raise HTTPException(status_code=404, detail="Log file is empty")
        
        messages = conversation_log.split('--------------------------------------------------------------------------------')
        # Iterate backwards through the messages to find the last one in the desired format
        for message in reversed(messages):
            if is_desired_format(message):
                last_message_of_format = message
                break
        # Split the last message into lines and filter out lines that start with 'INFO:'
        filtered_lines = [line for line in last_message_of_format.split('\n') if not line.startswith('INFO:') and line.strip()]

        # Join the filtered lines back into a single string
        filtered_message = '\n'.join(filtered_lines)


        # print("INFO: LAST MESSAGE in LAST MESSAGE API: ", filtered_message)
        
        # Return the last message
        return {"last_message": filtered_message}

    except Exception as e:
        # Handle any exceptions that occur
        raise HTTPException(status_code=500, detail=str(e))

