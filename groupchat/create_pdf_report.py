# filename: create_pdf_report.py

from fpdf import FPDF

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'App Components, STRIDE Threats, and Mitigations', 0, 1, 'C')

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(10)

    def chapter_body(self, body):
        self.set_font('Arial', '', 12)
        self.multi_cell(0, 10, body)
        self.ln()

    def add_component(self, title, body):
        self.add_page()
        self.chapter_title(title)
        self.chapter_body(body)

pdf = PDF()
components = {
    'Amazon Cognito': 'Spoofing: Unauthorized users may pretend to be legitimate users. Mitigation: Implement multi-factor authentication.\nTampering: User data could be altered during transmission. Mitigation: Use secure and encrypted connections.\nInformation Disclosure: Sensitive user data could be exposed to unauthorized users. Mitigation: Encrypt sensitive data.',
    'Amazon S3': 'Tampering: Game assets could be altered. Mitigation: Implement version control and backup systems.\nInformation Disclosure: Game assets could be exposed to unauthorized users. Mitigation: Use access control lists and bucket policies to restrict access.\nDenial of Service: Service could be disrupted, preventing access to game assets. Mitigation: Use AWS Shield for DDoS protection.',
    'DynamoDB': 'Tampering: Game state data could be altered. Mitigation: Implement access controls and monitor activity.\nInformation Disclosure: Game state data could be exposed to unauthorized users. Mitigation: Encrypt sensitive data.\nDenial of Service: Service could be disrupted, preventing updates to game state. Mitigation: Use AWS Shield for DDoS protection.',
    'AWS Lambda': 'Tampering: In-game event processing could be altered. Mitigation: Implement access controls and monitor activity.\nDenial of Service: Service could be disrupted, preventing processing of in-game events. Mitigation: Use AWS Shield for DDoS protection.',
    'GameLift': 'Spoofing: Unauthorized users may pretend to be legitimate users in multiplayer events. Mitigation: Implement player authentication and session management.\nDenial of Service: Service could be disrupted, preventing multiplayer gameplay. Mitigation: Use AWS Shield for DDoS protection.',
    'AppSync': 'Tampering: Offline play data could be altered during sync. Mitigation: Implement access controls and monitor activity.\nInformation Disclosure: Offline play data could be exposed to unauthorized users. Mitigation: Encrypt sensitive data.',
    'AWS Analytics': 'Information Disclosure: User behavior and game interaction data could be exposed to unauthorized users. Mitigation: Implement access controls and data anonymization techniques.',
    'Amazon Pinpoint': 'Spoofing: Unauthorized users may send push notifications pretending to be from the app. Mitigation: Implement access controls and monitor activity.\nInformation Disclosure: User engagement data could be exposed to unauthorized users. Mitigation: Encrypt sensitive data.'
}

for title, body in components.items():
    pdf.add_component(title, body)

pdf.output('AppComponentsSTRIDEThreatsAndMitigations.pdf')