# write a function that trims the whitespace from a string and adds a suffix "whats up ori"

def trim_and_add_suffix(string):
    return string.strip() + " whats up ori"

# write a function that does input sanitization from a json input that contains HIPPA data. Return an alert if theres an issue
def sanitize_input(json):
    if json["data"] == "HIPPA":
        return "ALERT"
    else:
        return json["data"]
    
# Sanitize the PII from a given json that looks like {"dob": "01/01/2000", "ssn": "123-45-6789", "name": "John Doe"}
def sanitize_pii(json):
    # first check if the json contains PII

    return json
