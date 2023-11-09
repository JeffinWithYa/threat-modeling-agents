#!/usr/bin/env python3

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

if __name__ == "__main__":
    tm.process()
