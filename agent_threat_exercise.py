import autogen
from pdf_reports import pug_to_html, write_report

config_list_gpt4 = autogen.config_list_from_json(
    "OAI_CONFIG_LIST",
    file_location=".",
    filter_dict={
        "model": ["gpt-4"],
    },
)

gpt4_config = {
    "seed": 49,  # change the seed for different trials
    "temperature": 0,
    "config_list": config_list_gpt4,
    "functions": [
        {
            "name": "report",
            "description": "Fill the template with the results of the threat modeling exercise. Executive summary contains priorities, and stride results is a dictionary of threats and mitigations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {
                        "type": "object",
                        "description": "110 words max summarizing the results of the threat modeling exercise and identifying the top priorities for immediate action.",
                    },
                "required": ["summary"],
                },
            },
        }
    ],
    "request_timeout": 120,
    "retry_wait_time": 88,
    

}

def create_report(summary):
    important_message_body = summary

    # Pass the variables to the Pug template
    html = pug_to_html("template.pug", 
                       important_message_body=important_message_body,
                       )

    # Generate the report
    write_report(html, "stride_report.pdf")

facilitator = autogen.UserProxyAgent(
    name="Threat-Modeling-Facilitator",
    is_termination_msg=lambda x: x.get("content", "") and x.get("content", "").rstrip().endswith("TERMINATE"),
    human_input_mode="NEVER",
    code_execution_config={"last_n_messages": 3, "work_dir": "groupchat", "use_docker": False},
    max_consecutive_auto_reply=3,

)
reporter = autogen.AssistantAgent(
    name="Reporter",
    system_message="For coding tasks, only use the functions you have been provided with. Reply TERMINATE when the task is done.",
    llm_config=gpt4_config,
)
# register the functions
facilitator.register_function(
    function_map={
        "report": create_report
    }
)

# start the conversation
#facilitator.initiate_chat(
#    reporter,
#    message="Create an executive summary with highest priority items based on this threat modeling exercise: The threat modeling exercise should include: identificaiton of all app components, STRIDE threats on each component, and mitigations for each STRIDE Threat:  User launches the app and logs in or registers via Amazon Cognito. Game assets required for play are fetched from Amazon S3. As the user plays, their game state (score, resources, etc.) is continuously updated in DynamoDB. Certain in-game events trigger AWS Lambda functions for processing. If users participate in multiplayer events, GameLift ensures seamless gameplay. Offline plays are synced back to DynamoDB using AppSync once the user is online. User behavior and game interactions are continuously sent to AWS Analytics for evaluation and insights. Amazon Pinpoint engages users with timely and relevant push notifications.",
#)
# groupchat = autogen.GroupChat(agents=[user_proxy, engineer, facilitator, pen_tester, stakeholder, critic], messages=[], max_round=50)
groupchat = autogen.GroupChat(agents=[facilitator, reporter], messages=[], max_round=50)
manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=gpt4_config)

facilitator.initiate_chat(manager, message="Create an executive summary with highest priority items based on this threat modeling exercise: The threat modeling exercise should include: identificaiton of all app components, STRIDE threats on each component, and mitigations for each STRIDE Threat:  User launches the app and logs in or registers via Amazon Cognito. Game assets required for play are fetched from Amazon S3. As the user plays, their game state (score, resources, etc.) is continuously updated in DynamoDB. Certain in-game events trigger AWS Lambda functions for processing. If users participate in multiplayer events, GameLift ensures seamless gameplay. Offline plays are synced back to DynamoDB using AppSync once the user is online. User behavior and game interactions are continuously sent to AWS Analytics for evaluation and insights. Amazon Pinpoint engages users with timely and relevant push notifications.")
