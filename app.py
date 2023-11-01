import autogen

config_list_gpt4 = autogen.config_list_from_json(
    "OAI_CONFIG_LIST",
    file_location=".",
    filter_dict={
        "model": ["gpt-4"],
    },
)

gpt4_config = {
    "seed": 50,  # change the seed for different trials
    "temperature": 0,
    "config_list": config_list_gpt4,
    "request_timeout": 120,
    "retry_wait_time": 88
}
user_proxy = autogen.UserProxyAgent(
   name="Admin",
   system_message="A human admin. Interact with the planner to discuss the plan. Plan execution needs to be approved by this admin.",
   code_execution_config=False,
   max_consecutive_auto_reply=4,
   is_termination_msg=lambda x: x.get("content", "") and x.get("content", "").rstrip().endswith("TERMINATE"),

)
engineer = autogen.AssistantAgent(
    name="Engineer",
    llm_config=gpt4_config,
    system_message='''Engineer. You understand the implementation details of the system. 
    With your expertise, you can pinpoint potential coding pitfalls that might lead to vulnerabilities and suggest possible solutions.
    You assist in identifying threats related to implementation details and provide mitigation strategies based on coding best practices.
    Reply TERMINATE when the task is done.

''',
)
facilitator = autogen.AssistantAgent(
    name="Threat-Modeling-Facilitator",
    llm_config=gpt4_config,
    system_message="""Threat Modeling Facilitator. You are working on a threat modeling exercise. You share a common interest in identifying potential threats in the proposed system and addressing them.
    Your main responsibilities include guiding the team through the threat modeling process, ensuring every potential threat is considered, and maintaining the flow of the exercise. Suggest a plan/exercise. 
    Revise the plan based on feedback from admin and critic, until admin approval.
The plan may involve an engineer who can point out coding pitfalls, a security architect who can highlight weak points in the architecture, a business stakeholder who can explain critical assets
and the business impacts of potential threats while prioritizing mitigations based on business needs, a pen tester who suggests testing methodologies for validating identified threats, and a compliance officer who ensures the exercise aligns with regulatory requirements.
Explain the plan first. Be clear which step is performed by an engineer, and which step is performed by a scientist. You provide a structured approach for the team to identify, prioritize, and address potential threats based on your expertise. Reply TERMINATE when the task is done."""
)
architect = autogen.AssistantAgent(
    name="Security-Architect",
    system_message='''Security Architect. You provide insights into the system's architecture, ensuring all components and their interactions are well-understood. 
    You also bring attention to potential weak points in the architecture where threats may exploit. Using your knowledge, you help identify potential weak points in the system and 
    propose architectural changes to mitigate threats. Reply TERMINATE when the task is done.
''',
    llm_config=gpt4_config,
)

pen_tester = autogen.AssistantAgent(
    name="Penetration-Tester",
    system_message='''Penetration Tester. You have knowledge about how to simulate potential attacks on the system, providing a real-world perspective on how threats might be exploited. 
    You also suggest testing methodologies for validating identified threats. You recommend potential attack vectors and methodologies to validate the identified threats, helping the team understand the real-world risks.
    Reply TERMINATE when the task is done.
''',
    llm_config=gpt4_config,
)
"""
compliance = autogen.AssistantAgent(
    name="Compliance-Officer",
    system_message='''Compliance Officer. You ensure that the threat modeling exercise aligns with regulatory requirements and standards. 
    Your role is crucial to ensure that identified threats and their mitigation don't put the organization at risk of non-compliance.
    You guide the team to ensure that our threat modeling and subsequent mitigation align with compliance standards and regulations.
    Reply TERMINATE when the task is done.
''',
    llm_config=gpt4_config,
)

stakeholder = autogen.AssistantAgent(
    name="Business-Stakeholder",
    system_message='''Business Stakeholder. Your main responsibility is to provide the business context. You explain the critical assets, business impacts of potential threats, and help prioritize mitigation based on business needs.
    You share the potential business implications of identified threats and guide the team in aligning security priorities with business objectives. Reply TERMINATE when the task is done.
''',
    llm_config=gpt4_config,
)
"""

critic = autogen.AssistantAgent(
    name="Critic",
    system_message='''Critic. Double check plan, claims, comments from other agents and provide feedback. Check whether the plan includes elucidating components, identifying threats, and proposing mitigations.
    Reply TERMINATE when the task is done.''',
    llm_config=gpt4_config,
)
# groupchat = autogen.GroupChat(agents=[user_proxy, engineer, facilitator, pen_tester, stakeholder, critic], messages=[], max_round=50)
groupchat = autogen.GroupChat(agents=[user_proxy, engineer, facilitator, pen_tester, critic], messages=[], max_round=50)
manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=gpt4_config)

user_proxy.initiate_chat(
    manager,
    message="""
Do a threat modeling exercise on this app:  User launches the app and logs in or registers via Amazon Cognito. Game assets required for play are fetched from Amazon S3. As the user plays, their game state (score, resources, etc.) is continuously updated in DynamoDB. Certain in-game events trigger AWS Lambda functions for processing. If users participate in multiplayer events, GameLift ensures seamless gameplay. Offline plays are synced back to DynamoDB using AppSync once the user is online. User behavior and game interactions are continuously sent to AWS Analytics for evaluation and insights. Amazon Pinpoint engages users with timely and relevant push notifications.
""",
)