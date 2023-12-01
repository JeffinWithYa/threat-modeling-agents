# Threat Modeling with Multi-Agent Generative AI - Backend APIs

This is an open source tool that is a FastAPI which uses the Autogen multi-agent framework and GPT4 to help working professionals quickly generate data flow diagrams, attack trees, and threat modeling reports from a description of their app architectures.

Features:

- Provide a description of your app architecture, and the tool will generate a data flow diagram using PyTM and Graphviz
- Identify the various components of your app from its description, and understand the vulnerabilities on each component using the STRIDE framework
- Get PDF reports summarizing the STRIDE vulnerabilities on your app's components
- Get PDF reports that include perspectives from technical and non-technical AI stakeholders, representing these roles in a threat modeling exercise

See the examples directory for example outputs (images, pdfs) from each API

### Prerequisites

### Set up the micfrontendroservices. See threat-modeling-agents-frontend repo (below) for details

```shell
git clone https://github.com/JeffinWithYa/threat-modeling-agents-frontend
```

### Cloning the repository

```shell
git clone https://github.com/JeffinWithYa/threat-modeling-agents-frontend
```

### Build container for each microservice API

```shell
docker build -t <service-name> .
```

### Run container with environment variables

```shell
docker run --name dfdcontainer --network threat_modeling_network -e OAI_CONFIG_LIST='[{"model": "gpt-4-1106-preview", "api_key": "<your-openai-api-key>"}]' -e FASTAPI_KEY='<your-unique-key-for-client-communication>' -e DATABASE_URL='<your-database-url>' -p 4000:81 dfd-service
```
