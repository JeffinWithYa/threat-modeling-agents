
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

tm = TM("Web Application Data Flow")
tm.description = "Threat model for a web application architecture with AWS services."
tm.isOrdered = True
tm.mergeResponses = True

internet = Boundary("Internet")

aws_cloud = Boundary("AWS Cloud")

user = Actor("User")
user.inBoundary = internet

route53 = ExternalEntity("Amazon Route 53")
route53.inBoundary = aws_cloud

elb = Process("Elastic Load Balancer")
elb.inBoundary = aws_cloud

ec2_instances = Process("EC2 Instances")
ec2_instances.inBoundary = aws_cloud

elastic_beanstalk = Process("AWS Elastic Beanstalk")
elastic_beanstalk.inBoundary = aws_cloud

rds = Datastore("Amazon RDS")
rds.inBoundary = aws_cloud

dynamodb = Datastore("Amazon DynamoDB")
dynamodb.inBoundary = aws_cloud

lambda_function = Lambda("AWS Lambda")
lambda_function.inBoundary = aws_cloud

s3 = Datastore("Amazon S3")
s3.inBoundary = aws_cloud

elasticache = Datastore("Amazon ElastiCache")
elasticache.inBoundary = aws_cloud

# Data definitions
http_request = Data("HTTP Request")
processed_data = Data("Processed Data")
json_response = Data("JSON Response")

# Dataflows
user_to_route53 = Dataflow(user, route53, "Send HTTP Request")
route53_to_elb = Dataflow(route53, elb, "Route to ELB")
elb_to_ec2 = Dataflow(elb, ec2_instances, "Direct to Appropriate EC2")
ec2_to_rds = Dataflow(ec2_instances, rds, "Query RDS Database")
ec2_to_dynamodb = Dataflow(ec2_instances, dynamodb, "Query DynamoDB Table")
ec2_to_lambda = Dataflow(ec2_instances, lambda_function, "Trigger Lambda Function")
ec2_to_s3 = Dataflow(ec2_instances, s3, "Interact with S3 Storage")
ec2_to_elasticache = Dataflow(ec2_instances, elasticache, "Access ElastiCache")
ec2_to_user = Dataflow(ec2_instances, user, "Send Response to User")

if __name__ == "__main__":
    tm.process()
    