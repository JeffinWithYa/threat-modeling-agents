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
dot.render('attack_tree.png', view=True)