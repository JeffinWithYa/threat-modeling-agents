from fastapi import FastAPI, HTTPException, Response, status, Depends, Header, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import subprocess
import autogen
import sys
import re
from pdf_reports import pug_to_html, write_report
from databases import Database
import ssl
import uuid
from concurrent.futures import ThreadPoolExecutor
import asyncio
from typing import Any, Dict, List, Optional, Union
from autogen import Agent


executor = ThreadPoolExecutor(max_workers=4)  # Adjust based on your needs
sys_message = """Using only the functions available to you, you create data flow diagrams by writing a pytm script to a file and outputting the data flow diagram. The pytm script is being injected into a template, so do not write any imports, with statements, or a main function. Here is an example pytm script that you should base your output off of. Note that it first defines the app components, and then how data flows between them. You should only pass 3 arguments to DataFlow().: 
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
            """


class ThreatModelingAgent(autogen.AssistantAgent):
    def __init__(self, task_id):
        super().__init__(
            name="chatbot",
            system_message=sys_message,    
            llm_config=llm_config,
            max_consecutive_auto_reply=10,
        )
        #self.register_reply(autogen.ConversableAgent, ThreatModelingAgent._update_db)
        self.task_id = ""




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
                    "task_id": {
                        "type": "string",
                        "description": "The task id for the current task.",
                    }
                },
                "required": ["cell", "task_id"],
            },
            
        },
    ],
    "config_list": config_list,
    "seed": 79,  # change the seed for different trials

}


# define functions according to the function desription

def exec_python(cell, task_id):
    
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

    print("INFO: pytm File written successfully")
    exec_sh("sh", task_id)

        # Create PDF
    agent_discussion = ""
    total_cost = 0
    total_input = 0
    total_output = 0
    original_prompt = ""
    log_file = "conversation_" + task_id + ".log"
    with open(log_file, "r") as f:
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
    pdf_path = "dfd_report_" + task_id + ".pdf"
    write_report(html, pdf_path)
    return "Report generated successfully"
    


def exec_sh(script, task_id):
    # The command you want to execute
    command = "python3 pytm_script.py --dfd | dot -Tsvg -o tm/" + task_id + "dfd.svg"
    
    # Execute the command
    process = subprocess.Popen(
        command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    # Wait for the command to complete
    stdout, stderr = process.communicate()

    # Check if the command was successful
    if process.returncode == 0:
        print("INFO: Command executed successfully.")
        #print(stdout.decode())
    else:
        print("INFO: An error occurred while executing the command.")
        #print(stderr.decode())



def initiate_chat_blocking(task_id: str, request_description: str):

    chatbot = ThreatModelingAgent(
        task_id=task_id
    )

    # create a UserProxyAgent instance named "user_proxy"
    user_proxy = autogen.UserProxyAgent(
        name="user_proxy",
        is_termination_msg=lambda x: x.get("content", "") and x.get("content", "").rstrip().endswith("TERMINATE"),
        human_input_mode="NEVER",
        max_consecutive_auto_reply=5,
        code_execution_config={"work_dir": "coding"},
    )
        # register the functions
    user_proxy.register_function(
        function_map={
            "python": exec_python        
        }
    )
    message = "Create a data flow diagram for the following app architecture: " + request_description + "DESCRIPTION_END" + ". When calling functions, use task_id: " + task_id + " as the second argument."

    # Start the conversation with the user proxy
    sys.stdout = DualOutput(f'conversation_{task_id}.log')
    print("INFO: STARTING CONVERSATION: ", message)

    user_proxy.initiate_chat(
        chatbot,
        message=message
    )
    sys.stdout.log.close()
    sys.stdout = sys.stdout.terminal

async def generate_diagram_background(task_id: str, request_description: str):
    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(executor, initiate_chat_blocking, task_id, request_description)
        image_path = f"tm/{task_id}dfd.svg"
        print("INFO:\n\nIMAGE PATH: ", image_path)

        # Update the task status to completed and set the file path in the database
        await database.execute("UPDATE TaskStatus SET status = :status, filePath = :filePath, updatedAt = NOW() WHERE id = :id", {"id": task_id, "status": "completed", "filePath": image_path})


    except Exception as e:
        #print(e)
        # Update the task status to failed in the database
        await database.execute("UPDATE TaskStatus SET status = :status, updatedAt = NOW() WHERE id = :id", {"id": task_id, "status": "failed"})

def is_desired_format(message):
    return re.search(r'.* \(to .*\):', message) is not None


# Define your Pydantic model for request validation
class DiagramRequest(BaseModel):
    description: str

def validate_api_key(x_api_key: str = Header(...)):
    #print("\n\nValidating API key\n\n")
    expected_api_key = os.getenv("FASTAPI_KEY")  # Get API key from environment variable
    if not expected_api_key or x_api_key != expected_api_key:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return x_api_key

# Create a FastAPI instance
app = FastAPI()

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

# Other configurations and function definitions remain the same...

@app.post('/generate-diagram')
async def generate_diagram(request: DiagramRequest, background_tasks: BackgroundTasks, api_key: str = Depends(validate_api_key)):
    task_id = str(uuid.uuid4())
    await database.execute("INSERT INTO TaskStatus (id, status, createdAt, updatedAt) VALUES (:id, :status, NOW(), NOW())", {"id": task_id, "status": "pending"})
    background_tasks.add_task(generate_diagram_background, task_id, request.description)
    return {"task_id": task_id}

@app.post('/generate-diagram-pdf')
async def generate_diagram(request: DiagramRequest, api_key: str = Depends(validate_api_key)):
    try:
        message = "Create a data flow diagram for the following app architecture: " + request.description + "DESCRIPTION_END"
        task_id = str(uuid.uuid4())


        # Start the conversation with the user proxy
        sys.stdout = DualOutput('conversation.log')
        print("INFO: STARTING CONVERSATION: ", message)
        chatbot = ThreatModelingAgent(
            task_id=task_id
        )

        # create a UserProxyAgent instance named "user_proxy"
        user_proxy = autogen.UserProxyAgent(
            name="user_proxy",
            is_termination_msg=lambda x: x.get("content", "") and x.get("content", "").rstrip().endswith("TERMINATE"),
            human_input_mode="NEVER",
            max_consecutive_auto_reply=5,
            code_execution_config={"work_dir": "coding"},
        )
            # register the functions
        user_proxy.register_function(
            function_map={
                "python": exec_python        
            }
        )

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

@app.get("/get-diagram/{task_id}")
async def get_diagram(task_id: str, api_key: str = Depends(validate_api_key)):
    query = "SELECT status, filePath FROM TaskStatus WHERE id = :task_id"
    result = await database.fetch_one(query, {"task_id": task_id})

    if result is None:
        raise HTTPException(status_code=404, detail="Task not found")

    task_status, image_path = result['status'], result['filePath']
    print("INFO: TASK STATUS in POLL: ", task_status)

    if task_status == "completed":
        attempts = 0
        max_attempts = 5  # For example, retry 5 times
        delay_seconds = 2  # Wait for 2 seconds between each retry

        while not os.path.exists(image_path) and attempts < max_attempts:
            print(f"Waiting for file to be available. Attempt {attempts + 1}")
            await asyncio.sleep(delay_seconds)  # Async sleep for non-blocking wait
            attempts += 1

        if os.path.exists(image_path):
            return FileResponse(image_path, media_type='image/svg+xml')
        else:
            raise HTTPException(status_code=404, detail="Image not found or task failed")
    elif task_status == "pending":
        raise HTTPException(status_code=202, detail="Task is still processing")
    else:
        raise HTTPException(status_code=404, detail="Task failed or invalid status")

    

@app.post('/generate-diagram-direct')
async def generate_diagram(request: DiagramRequest, api_key: str = Depends(validate_api_key)):
    try:
        task_id = str(uuid.uuid4())
        await database.execute("INSERT INTO TaskStatus (id, status, createdAt, updatedAt) VALUES (:id, :status, NOW(), NOW())", {"id": task_id, "status": "pending"})


        message = "Create a data flow diagram for the following app architecture: " + request.description + "DESCRIPTION_END" + ". When calling functions, use task_id: " + task_id + " as the second argument."

        # Start the conversation with the user proxy
        sys.stdout = DualOutput(f'conversation_{task_id}.log')
        print("INFO: STARTING CONVERSATION: ", message)

        # create a UserProxyAgent instance named "user_proxy"
        user_proxy = autogen.UserProxyAgent(
            name="user_proxy",
            is_termination_msg=lambda x: x.get("content", "") and x.get("content", "").rstrip().endswith("TERMINATE"),
            human_input_mode="NEVER",
            max_consecutive_auto_reply=5,
            code_execution_config={"work_dir": "coding"},
        )
                # register the functions
        user_proxy.register_function(
            function_map={
                "python": exec_python        
            }
        )
        chatbot = ThreatModelingAgent(
            task_id=task_id
        )


        user_proxy.initiate_chat(
            chatbot,
            message=message
        )
        sys.stdout.log.close()
        sys.stdout = sys.stdout.terminal

        image_path = f"tm/{task_id}dfd.svg"
        await database.execute("UPDATE TaskStatus SET status = :status, filePath = :filePath, updatedAt = NOW() WHERE id = :id", {"id": task_id, "status": "completed", "filePath": image_path})


        if os.path.exists(image_path):
            return FileResponse(image_path, media_type='image/svg')
        else:
            raise HTTPException(status_code=404, detail="Image not found")

    except Exception as e:
        #print(e)
        raise HTTPException(status_code=500, detail=str(e))
    
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


        #print("INFO: LAST MESSAGE in LAST MESSAGE API: ", filtered_message)
        
        # Return the last message
        return {"last_message": filtered_message}

    except Exception as e:
        # Handle any exceptions that occur
        raise HTTPException(status_code=500, detail=str(e))

