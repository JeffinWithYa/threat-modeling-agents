from pytm import TM, Server, Dataflow, Boundary, Actor, Lambda

tm = TM("Web Application Attack Tree")
tm.description = "Attack tree modeling for a web application hosted on AWS."

user = Actor("User")
web_frontend = Server("Web Frontend")
aws_route53 = Server("AWS Route 53")
load_balancer = Server("Elastic Load Balancer")
ec2_instance = Server("EC2 Instance")
elastic_beanstalk = Server("AWS Elastic Beanstalk")
rds = Server("Amazon RDS")
dynamodb = Server("Amazon DynamoDB")
lambda_function = Lambda("AWS Lambda")
s3 = Server("Amazon S3")
elasticache = Server("Amazon ElastiCache")
internet = Boundary("Internet")
aws_network = Boundary("AWS Network")

# Defining data flows
user_to_frontend = Dataflow(user, web_frontend, "HTTP Request")
frontend_to_route53 = Dataflow(web_frontend, aws_route53, "DNS Query")
route53_to_elb = Dataflow(aws_route53, load_balancer, "Route to ELB")
elb_to_ec2 = Dataflow(load_balancer, ec2_instance, "Load Balanced Traffic")
ec2_to_rds = Dataflow(ec2_instance, rds, "DB Query")
ec2_to_dynamodb = Dataflow(ec2_instance, dynamodb, "DB Query")
ec2_to_lambda = Dataflow(ec2_instance, lambda_function, "Trigger Lambda")
ec2_to_s3 = Dataflow(ec2_instance, s3, "S3 Object Access")
ec2_to_elasticache = Dataflow(ec2_instance, elasticache, "Cache Access")
response_to_user = Dataflow(ec2_instance, user, "HTTP Response")

# Setting trust boundaries
#internet.add_flow(user_to_frontend, response_to_user)
#aws_network.add_flow(frontend_to_route53, route53_to_elb, elb_to_ec2, ec2_to_rds, ec2_to_dynamodb, ec2_to_lambda, ec2_to_s3, ec2_to_elasticache)

# Define attack tree
#steal_user_data = Threat("Steal User Data")
# Add branches to the attack tree here...

if __name__ == "__main__":
    tm.process()
