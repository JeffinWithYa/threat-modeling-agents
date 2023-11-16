from pdf_reports import pug_to_html, write_report

# Define your variables
hostile_vetrts_logo = '/Users/jeffreyjeyachandren/Desktop/threat-modeling-agents/threat-modeling-agents/threat_agents_team.svg'  # Ensure this is the correct file path.
STRIDE_Threats_and_Mitigations = 'Stride Threats and Mitigations'
important_message_body = """
    The STRIDE analysis of our game app's architecture unearthed critical security issues: a spoofing risk within user authentication, a tampering threat to in-app purchases, potential for sensitive data leaks, and vulnerability to Denial of Service (DoS) attacks.
    Top priorities for immediate action are:
        Implementing multi-factor authentication to counteract spoofing.
        Enhancing encryption for in-app transactions to prevent tampering.
        Securing data transfers to avert information leaks.
        Fortifying the leaderboard server against DoS attacks.
        Addressing these concerns is crucial for maintaining robust security and user trust. Immediate remediation will not only protect users but also fortify the app's integrity and market reputation."
"""
#table_rows = 

important_message_header = "Executive Summary"
# Pass the variables to the Pug template
"""
html = pug_to_html("template_playground.pug", 
                   hostile_vetrts_logo=hostile_vetrts_logo,
                   important_message_body=important_message_body,
                   important_message_header=important_message_header)
"""


pug_string = """img(style="width:200px; display:block; margin:0 auto; opacity:1;" src="file:///usr/src/app/threat_agents_team.svg")
#sidebar

.ui.stacked.segment.inverted.grey: p.
  This is an auto-generated Threat Modeling Report, assembled by GPT-4 Threat Modeling Agents. 
  The system reviews the specified application architecture. 
  It applies the STRIDE methodology to each component, providing a thorough evaluation of potential security threats, but may still contain errors.
  
.ui.container
  .ui.icon.message.blue.block-center
    i.exclamation.circle.icon
    .content
      .header Executive Summary
      p.
        {{ important_message_body }}


:markdown
    ## Results
table.ui.celled.table
    thead
    tr
        th Role
        th Analysis
    tbody

      tr
        td Architecture
        td
          | Architecture Discussion:
          | 
          | The comprehensive reports provided by both the engineering and architectural teams, which have examined the STRIDE and DREAD results, bring to light critical vulnerabilities that need to be addressed to fortify the web application's resilience against threats. The web application, despite its robust feature set, demonstrates areas within its design that can potentially be exploited. To address these weak points, several architectural changes are proposed.
          | 
          | 1. **Spoofing Identity**: The authentication process managed by Flask-Login could be bolstered through multifactor authentication or integration with more sophisticated identity providers that enforce strict authentication measures.
          | 
          | 2. **Tampering with Data**: The libraries used for forms (WTForms, Flask-WTF, Flask-Bootstrap, Flask-Admin, Flask-RESTful) need to be secure against various injection attacks. Input validation and output encoding should be systematically used to prevent data tampering.
          | 
          | 3. **Repudiation**: With the intent to provide a non-repudiable proof of actions taken within the application, it is essential to integrate a comprehensive logging solution that is well protected against tampering. Services like AWS CloudTrail can effectively record and maintain immutable logs.
          | 
          | 4. **Information Disclosure**: Encrypting data at rest and in transit, employing services such as AWS RDS for managed database solutions with built-in encryption, and utilizing AWS Key Management Service for managing encryption keys can greatly mitigate the risk of leakage of sensitive data.
          | 
          | 5. **Denial of Service (DoS)**: To protect the application from DoS attacks, implementing scalable solutions is key. AWS Auto Scaling and Elastic Load Balancing can ensure that the application scales in response to traffic demands, while AWS WAF and Shield can provide added layers of protection.
          | 
          | 6. **Elevation of Privilege**: Properly implemented role-based access controls, with the principle of least privilege, must be ensured both at the AWS infrastructure level using IAM best practices and within the application's own authorization logic.
          | 
          | Architectural Improvements:
          | 
          | - Transitioning the data storage to AWS RDS to leverage advanced security features.
          | - Configuring AWS EC2 instances with auto-scaling and robust security group settings.
          | - Implementing security incident management processes using AWS CloudWatch alongside AWS Lambda for automated alerts and responses.
          | - Exploring serverless architectures for certain application components to reduce the attack surface and offload security compliance to AWS.
          | - Rigorous application of IAM best practices, including the rotation of keys and the segregation of duties in privileged operations.
          | 
          | By addressing these vulnerabilities and implementing the architectural improvements, the application will show vastly improved defenses against malicious actions. Regularly revisiting these decisions and keeping up with new security advancements and threats will solidify our posture in an ever-changing security landscape.
          | 
          | End of Architecture Discussion.

      tr
        td Engineering
        td
          | Engineering Discussion:
          | 
          | The STRIDE and DREAD analyses have indeed highlighted crucial vulnerabilities that we must address. The proposed architectural strategies from A3 provide a secure framework upon which the following engineering practices can further fortify the application against those vulnerabilities.
          | 
          | 1. **Spoofing Identity**: To ensure secure authentication, the engineering team should implement best practices such as using HTTPS across the site by default, considering using a more sophisticated authentication system like OAuth, and implementing multi-factor authentication wherever applicable.
          | 
          | 2. **Tampering with Data**: We must utilize the form validation capabilities of WTForms and Flask-WTF effectively to avoid tampering. Data going into the database must use ORM or prepared statements to minimize the risk of SQL Injection, which can also be prevented with database management solutions such as AWS RDS.
          | 
          | 3. **Repudiation**: Immutability in logging can be enhanced through the use of secure logging mechanisms that prevent logs from being altered or deleted after they've been recorded. This ensures a traceable activity log for any actions taken within the application.
          | 
          | 4. **Information Disclosure**: Sensitive data should be encrypted with industry-standard protocols both at rest (using encryption solutions suitable for databases like MySQL) and in transit (using secure and updated TLS configurations). Additionally, AWS services like KMS can be used to manage and rotate encryption keys securely.
          | 
          | 5. **Denial of Service (DoS)**: Implementing rate limiting at the application level using Flask-Limiter and at the infrastructure level using AWS services such as CloudFront and WAF can offer a strong line of defense against DoS attacks.
          | 
          | 6. **Elevation of Privilege**: Access control within the application must be strictly enforced. Regular code audits are essential to ensure that privilege elevation is not possible through exploits in code.
          | 
          | Critical Engineering Practices Include:
          | 
          | - Continuous Integration (CI) and Continuous Deployment (CD) pipeline that includes security testing and scanning for vulnerabilities.
          | - Frequent updates to dependencies and libraries to patch known vulnerabilities, and regular codebase audits for potential security issues.
          | - Adhering to the principle of least privilege at all levels of code and infrastructure to ensure minimal access rights to functions and data unless absolutely necessary.
          | - Encouraging a culture of security amongst the development team through regular training and awareness programs.
          | - Considering sandboxing environments for running code that interacts with untrusted data.
          | - Adopting a microservices architecture that, by design, isolates components and systems, reducing the potential impact of a single compromised service.
          | 
          | Implementing these engineering best practices and integrating them with the proposed architectural changes will lead to more comprehensive protection for our web application. Regular reviews and updates of these processes, guided by the ongoing results of STRIDE and DREAD analyses, will ensure the application's defense mechanisms evolve in line with the current threat landscape.
          | 
          | End of Engineering Discussion.


:markdown
    ## Appendix

B1 (to chat_manager):

Identify the components and attack vectors in this app architecture, and then get an analysis of each identified component/vector using STRIDE and DREAD. App architecture: The application architecture is a web application with a database. The web application is written in Python and uses the Flask framework. The database is a MySQL database. The web application is hosted on AWS EC2. The web application is a simple blog application that allows users to create posts and comment on posts. The web application uses a MySQL database to store the posts and comments. The web application uses the Flask framework to handle requests and responses. The web application uses the Jinja2 templating engine to render HTML templates. The web application uses the WTForms library to handle forms. The web application uses the Flask-Login library to handle user authentication. The web application uses the Flask-WTF library to handle forms. The web application uses the Flask-Bootstrap library to handle forms. The web application uses the Flask-Admin library to handle forms. The web application uses the Flask-RESTful library to handle forms.

--------------------------------------------------------------------------------
A1 (to chat_manager):

NEXT: B1

--------------------------------------------------------------------------------
Extracted suggested_next = B1
B1 (to chat_manager):

Hello A1,

I am reaching out to request an analysis of our current application architecture using the STRIDE and DREAD methodologies. Our team has identified the following components and potential attack vectors within this web application:

1. **Web Application (Python/Flask):**
   - Spoofing identity
   - Tampering with data
   - Repudiation threats
   - Information disclosure
   - Denial of Service (DoS)

"""


html = pug_to_html(string=pug_string, 
                   hostile_vetrts_logo=hostile_vetrts_logo,
                   important_message_body=important_message_body,
                   important_message_header=important_message_header)
# Generate the report
write_report(html, "your_stakeholder_report.pdf")
