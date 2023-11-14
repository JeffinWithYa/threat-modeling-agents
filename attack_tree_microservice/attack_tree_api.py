from fastapi import FastAPI, HTTPException, Response, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import subprocess
import autogen

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
    system_message="""Using only the functions available to you, you create attack tree diagrams by writing a script to a file and outputting the data flow diagram. Make sure you call the render function with 'attack_tree' and specify 'png' for format. Here is an example script that you should base your output off of: 
    # filename: attack_tree.py

from graphviz import Digraph

# Create a directed graph
dot = Digraph(comment='Attack Tree')

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

# Save the graph as a PNG file
dot.format = 'png'
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
# Define your Pydantic model for request validation
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
        message = "Create an attack tree diagram for the following app architecture, " + "with the top node being " + request.topnode + ". App architecture: " + request.description

        # Start the conversation with the user proxy
        user_proxy.initiate_chat(
            chatbot,
            message=message
        )

        image_path = 'attack_tree.png'

        if os.path.exists(image_path):
            return FileResponse(image_path, media_type='image/png')
        else:
            raise HTTPException(status_code=404, detail="Image not found")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# No need to specify host and port here, run with Uvicorn or similar ASGI server
