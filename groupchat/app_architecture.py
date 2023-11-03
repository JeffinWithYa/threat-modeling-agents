# filename: app_architecture.py

from graphviz import Digraph

dot = Digraph(comment='App Architecture')

# Add nodes
dot.node('A', 'User')
dot.node('B', 'Amazon Cognito')
dot.node('C', 'Amazon S3')
dot.node('D', 'DynamoDB')
dot.node('E', 'AWS Lambda')
dot.node('F', 'GameLift')
dot.node('G', 'AppSync')
dot.node('H', 'AWS Analytics')
dot.node('I', 'Amazon Pinpoint')

# Add edges with labels
dot.edge('A', 'B', label='Logs in/Registers')
dot.edge('B', 'C', label='Fetches game assets')
dot.edge('A', 'D', label='Updates game state')
dot.edge('D', 'E', label='Triggers Lambda functions')
dot.edge('A', 'F', label='Participates in multiplayer events')
dot.edge('A', 'G', label='Syncs offline plays')
dot.edge('A', 'H', label='Sends game interactions')
dot.edge('A', 'I', label='Receives push notifications')

# Save the graph in a PNG file
dot.format = 'png'
dot.render('app_architecture', view=True)