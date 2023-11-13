# filename: attack_tree.py

from graphviz import Digraph

# Create a new directed graph
dot = Digraph(comment='Attack Tree')

# Add the root node
dot.node('A', 'Stealing User\'s Data')

# Add child nodes representing potential attack vectors
dot.node('B', 'Amazon Cognito')
dot.node('C', 'Amazon S3')
dot.node('D', 'DynamoDB')
dot.node('E', 'AWS Lambda')
dot.node('F', 'GameLift')
dot.node('G', 'AppSync')
dot.node('H', 'AWS Analytics')
dot.node('I', 'Amazon Pinpoint')

# Add edges from the root node to each child node
dot.edges(['AB', 'AC', 'AD', 'AE', 'AF', 'AG', 'AH', 'AI'])

# Save the graph to a file
dot.format = 'png'
dot.render('attack_tree.png', view=True)