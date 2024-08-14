# Threat Modeling with Multi-Agent Generative AI - Backend APIs

This is an open source tool that is a FastAPI which uses the Autogen multi-agent framework and GPT4 to help working professionals quickly generate data flow diagrams, attack trees, and threat modeling reports from a description of their app architectures.

Features:

- Provide a description of your app architecture, and the tool will generate a data flow diagram using PyTM and Graphviz
- Identify the various components of your app from its description, and understand the vulnerabilities on each component using the STRIDE framework
- Get PDF reports summarizing the STRIDE vulnerabilities on your app's components
- Get PDF reports that include perspectives from technical and non-technical AI stakeholders, representing these roles in a threat modeling exercise

See the examples directory for example outputs (images, pdfs) from each API

### Prerequisites

### Set up the frontend. See threat-modeling-agents-frontend repo (below) for details

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

### Example of how to generate threat modeling report with Docker and Postman:
Clone the repo and navigate to the data_flow_diagram_microservice directory
```
git clone https://github.com/JeffinWithYa/threat-modeling-agents
cd data_flow_diagram_microservice
```
Build the container that creates data flow diagrams for the report
```
docker build -t dfd-service
```
Set the environment variables and run the dfd-service container
```
docker run --name dfdcontainer --network threat_modeling_network -e OAI_CONFIG_LIST='[{"model": "gpt-4-1106-preview", "api_key": "<YOUR-OPENAI-API-KEY>"}]' -e FASTAPI_KEY='<UNIQUE-KEY-YOU-CREATE-THATS-SHARED-BETWEEN-MICROSERVICES>' -e DATABASE_URL='<YOUR-PLANETSCALE-DATABASE-URL>' -p 4000:81 dfd-service
```
Navigate to the stride_report_microservice directory
```
cd ..
cd stride_report_microservice
```
Build the container that creates the STRIDE threat modeling reports
```
docker build -t stride-service .
```
Set the environment variables and run the stride-service container
```
docker run --name stridecontainer --network threat_modeling_network -e FASTAPI_KEY='<UNIQUE-KEY-YOU-CREATE-THATS-SHARED-BETWEEN-MICROSERVICES>' -e DFD_API_URL='http://dfdcontainer:8080/generate-diagram-direct' -e OAI_CONFIG_LIST='[{"model": "gpt-4-1106-preview", "api_key": "<YOUR-OPENAI-API-KEY>"}]' -e DATABASE_URL='<YOUR-PLANETSCALE-DATABASE-URL>' -e CONFIG_MODE='local' -p 4001:8080 stride-service
```
From Postman, request a Threat Modeling report by making a POST request to /generate-stride-report. Example:
```
http://127.0.0.1:4001/generate-stride-report
Add header to request 'x-api-key' = <UNIQUE-KEY-YOU-CREATE-THATS-SHARED-BETWEEN-MICROSERVICES>

Example body of request:
{
  "description": "When a user wants to play a media file using VLC, they begin by launching the VLC application from their device. The application is running on a local machine with a local user. Once the application is open, they navigate to the Media menu located at the top left of the interface. From the dropdown options, the user selects Open File which prompts a file explorer window to appear. They then browse through their directories to locate the desired media file, select it, and click Open. The selected file immediately starts playing in the VLC media player window. The user can use the on-screen controls to pause, play, adjust volume, skip forward or backward, and toggle fullscreen mode as needed. For additional adjustments, they can access various audio and video settings from the respective menus to enhance their viewing or listening experience."
}

POST request will return a unique task-id, which is used to retrieve the report once its ready.
```
Finally, from Postman, retrieve the report once its completed using the task-id returned from the previous request:
```
http://127.0.0.1:4001/get-stride/<task-id>

Don't forget to also add a header to this request: 'x-api-key' = <UNIQUE-KEY-YOU-CREATE-THATS-SHARED-BETWEEN-MICROSERVICES>

```

[View example of outputted Threat Modeling Report](https://github.com/JeffinWithYa/threat-modeling-agents/blob/main/examples/stride_report_api/stride_report_flask_blog.pdf)





