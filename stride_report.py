import autogen

config_list_gpt4 = autogen.config_list_from_json(
    "OAI_CONFIG_LIST",
    file_location=".",
    filter_dict={
        "model": ["gpt-4"],
    },
)
gpt4_config = {
    "seed": 48,  # change the seed for different trials
    "temperature": 0,
    "config_list": config_list_gpt4,
    "request_timeout": 120,
    "retry_wait_time": 10,
}

facilitator = autogen.AssistantAgent(
    name="Threat-Modeling-Facilitator",
    llm_config=gpt4_config,
    code_execution_config=False,
    system_message="""Threat Modeling Facilitator. You are working on doing a threat modeling exercise, where you identify the components of an app architecture and go through STRIDE for each component.
    Your main responsibilities include ensuring every potential threat is considered, and mitigations for each are discussed.
    In your discussions, consider coding pitfalls, weak points in the architecture, and testing methodologies for validating identified threats.
    """
)

user_proxy = autogen.UserProxyAgent(
   name="User_proxy",
   system_message="A human admin.",
   max_consecutive_auto_reply=2,
   code_execution_config={"last_n_messages": 3, "work_dir": "groupchat", "use_docker": False},
   human_input_mode="NEVER",
)
coder = autogen.AssistantAgent(
    name="Coder",  # the default assistant agent is capable of solving problems with code
    llm_config=gpt4_config,
)
critic = autogen.AssistantAgent(
    name="Critic",
    system_message="""Critic. You are a helpful assistant highly skilled in evaluating the quality of code to generate the threat report by providing a score from 1 (bad) - 10 (good) while providing clear rationale. Specifically, you can carefully evaluate the code across the following dimensions
- bugs (bugs):  are there bugs, logic errors, syntax error or typos? Are there any reasons why the code may fail to compile? How should it be fixed? If ANY bug exists, the bug score MUST be less than 5.
- Goal compliance (compliance): Make sure the PDF contains the app components, a discussion of their STRIDE threats, and mitigations. Don't just list out the stride threats for components. Explain how the threat is relevant to the component, and how the mitigation works.
- aesthetics (aesthetics): Are the aesthetics of the visualization appropriate for the visualization type and the data?

YOU MUST PROVIDE A SCORE for each of the above dimensions.
{bugs: 0, compliance: 0, aesthetics: 0}
Do not suggest code. 
Finally, based on the critique above, suggest a concrete list of actions that the coder should take to improve the code.
""",
    llm_config=gpt4_config,
)

groupchat = autogen.GroupChat(agents=[user_proxy, coder, critic, facilitator], messages=[], max_round=20)
manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=gpt4_config)

# user_proxy.initiate_chat(manager, message="download data from https://raw.githubusercontent.com/uwdata/draco/master/data/cars.csv and plot a visualization that tells us about the relationship between weight and horsepower. Save the plot to a file. Print the fields in a dataset before visualizing it.")
user_proxy.initiate_chat(manager, message="Create a pdf report with the python library fpdf2, which has a table of app components and STRIDE threats based on the given app architecture. Save the result as a pdf file. Here is the app architecture: User launches the app and logs in or registers via Amazon Cognito. Game assets required for play are fetched from Amazon S3. As the user plays, their game state (score, resources, etc.) is continuously updated in DynamoDB. Certain in-game events trigger AWS Lambda functions for processing. If users participate in multiplayer events, GameLift ensures seamless gameplay. Offline plays are synced back to DynamoDB using AppSync once the user is online. User behavior and game interactions are continuously sent to AWS Analytics for evaluation and insights. Amazon Pinpoint engages users with timely and relevant push notifications.")
