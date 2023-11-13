from fastapi import FastAPI, HTTPException, Response, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import subprocess
import autogen



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
    


def exec_sh(script):
    # The command you want to execute
    command = "python3 pytm_script.py --dfd | dot -Tpng -o tm/dfd.png"
    
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
        message = "Create a data flow diagram for the following app architecture: " + request.description

        # Start the conversation with the user proxy
        user_proxy.initiate_chat(
            chatbot,
            message=message
        )

        image_path = 'tm/dfd.png'

        if os.path.exists(image_path):
            return FileResponse(image_path, media_type='image/png')
        else:
            raise HTTPException(status_code=404, detail="Image not found")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# No need to specify host and port here, run with Uvicorn or similar ASGI server
