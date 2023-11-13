from flask import Flask, request, jsonify, send_file
app = Flask(__name__)

import os
import autogen
import subprocess


config_list = autogen.config_list_from_json(
    "OAI_CONFIG_LIST",
    file_location=".",
    filter_dict={
        "model": ["gpt-4-1106-preview"],
    },
)
llm_config = {
    "functions": [
        {
            "name": "python",
            "description": "Writes the pytm script to a file.",
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
        {
            "name": "sh",
            "description": "Creates the data flow diagram.",
            "parameters": {
                "type": "object",
                "properties": {
                    "script": {
                        "type": "string",
                        "description": "arbitrary message",
                    }
                },
                "required": ["script"],
            },
        },
    ],
    "config_list": config_list,
    "seed": 79,  # change the seed for different trials

}
chatbot = autogen.AssistantAgent(
    name="chatbot",
    system_message="""Using only the functions available to you, you create data flow diagrams by first creating a pytm script, and then call 'sh' with 'hello' to output the PNG. The pytm script is being injected into a template, so do not write any imports, with statements, or a main function. Here is an example pytm script that you should base your output off of. Note that it first defines the app components, and then how data flows between them: 
    tm = TM("Game App Data Flow")
tm.description = "Threat model for a game application architecture with AWS services."
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

dynamodb = Datastore("DynamoDB")
dynamodb.inBoundary = aws_cloud

lambda_function = Lambda("AWS Lambda")
lambda_function.inBoundary = aws_cloud

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
in_game_event = Data("In-game Event")
multiplayer_data = Data("Multiplayer Data")
offline_play = Data("Offline Play Data")
user_behavior = Data("User Behavior Data")
push_notification = Data("Push Notification")

# Dataflows
user_to_cognito = Dataflow(user, cognito, "User Authentication")
user_to_s3 = Dataflow(user, s3, "Fetch Game Assets")
user_to_dynamodb = Dataflow(user, dynamodb, "Update Game State")
user_to_lambda = Dataflow(user, lambda_function, "Trigger Lambda with Event")
user_to_gamelift = Dataflow(user, gamelift, "Participate in Multiplayer")
user_to_appsync = Dataflow(user, appsync, "Sync Offline Plays")
user_to_analytics = Dataflow(user, analytics, "Send Behavior Data")
user_to_pinpoint = Dataflow(user, pinpoint, "Receive Push Notifications") 

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
        "python": exec_python,
        "sh": exec_sh   
        }
)

@app.route('/')
def hello():
	return "Hello World!"

# example description:
# In a web application hosted on AWS, the data flow typically begins with the user's interaction with the front-end, which triggers an HTTP request. This request is routed through Amazon Route 53 to an Elastic Load Balancer, which then directs the traffic to the appropriate EC2 instances where the application is hosted. The application code, possibly running on an AWS Elastic Beanstalk environment, processes the request, which may include querying an Amazon RDS database or an Amazon DynamoDB table to retrieve or store data. AWS Lambda functions could also be utilized for serverless computation. The application may interact with additional AWS services like S3 for object storage, or use Amazon ElastiCache to access frequently requested data quickly. Once the server-side processing is complete, the data is formatted (often as JSON) and sent back through the Internet to the user's browser, where it is rendered, and any dynamic client-side actions are handled by JavaScript. This architecture benefits from the scalability, reliability, and security provided by AWS.

@app.route('/generate-diagram', methods=['POST'])
def generate_diagram():
     
    try:
        description = request.json.get('description')
        message = "Create a data flow diagram for the following app architecture: " + description

           
        # start the conversation
        user_proxy.initiate_chat(
            chatbot,
            message=message
        )

        # Assuming the PNG is saved at 'tm/dfd.png'
        image_path = 'tm/dfd.png'

        # Check if the file exists
        if os.path.exists(image_path):
            return send_file(image_path, mimetype='image/png')
        else:
            return jsonify({"error": "Image not found"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8002)
