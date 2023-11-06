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
important_message_header = "Executive Summary"
# Pass the variables to the Pug template
html = pug_to_html("template.pug", 
                   hostile_vetrts_logo=hostile_vetrts_logo,
                   important_message_body=important_message_body,
                   important_message_header=important_message_header)

# Generate the report
write_report(html, "your_report.pdf")
