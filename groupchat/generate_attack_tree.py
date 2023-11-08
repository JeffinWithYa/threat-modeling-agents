# filename: generate_attack_tree.py
import graphviz

# Create a new directed graph
dot = graphviz.Digraph(comment='Attack Tree', format='png')

# Add nodes and edges to the graph
dot.node('A', 'Steal Data from DynamoDB')
dot.node('B', 'Intercept AppSync Data')
dot.node('C', 'Exploit AWS Lambda')
dot.node('D', 'Attack Game State Update')
dot.node('E', 'Compromise Amazon Cognito')
dot.node('F', 'Sniff S3 Traffic')
dot.node('G', 'Exploit GameLift')
dot.node('H', 'Intercept AWS Analytics Data')
dot.node('I', 'Malicious Amazon Pinpoint Notifications')

dot.edges(['AB', 'AC', 'AD', 'AE', 'AF', 'AG', 'AH', 'AI'])

# Render the graph to a file
dot.render('attack_tree')

print("Attack tree visualization has been saved as 'attack_tree.png'")