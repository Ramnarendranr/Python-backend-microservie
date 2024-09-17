# Python-backend-microservice


This is a Python backend microservice built using Flask, designed to accept and execute user-submitted Python code in a Kubernetes environment. The service utilizes MongoDB to store execution metadata and results.

## Features

- **Code Execution**: Accepts base64-encoded Python code and executes it in a Kubernetes job.
- **Result Retrieval**: Users can retrieve the status and output of their submitted code executions.
- **Data Persistence**: Execution metadata and results are stored in a MongoDB database.

## Technologies Used

- Python 3.9
- Flask
- MongoDB
- Kubernetes
- Docker

## Getting Started

### Prerequisites

- Docker installed on your machine.
- Access to a Kubernetes cluster. (I'm using AWS EKS cluster)
- MongoDB instance (either local or cloud-based).
- Required Python packages listed in `requirements.txt`.

## DATABASE SELECTION - MONGODB
#### Why Choose MongoDB Atlas?

I chose MongoDB Atlas over a self-hosted MongoDB solution for several reasons:

- **Managed Service**: Atlas provides a fully managed database service, reducing the operational overhead of maintaining the database.
- **Scalability**: It offers easy scalability options to accommodate varying workloads without manual intervention.
- **Built-in Security**: Atlas includes features like automated backups, end-to-end encryption, and compliance with various security standards.
- **Global Reach**: It allows deploying databases across multiple cloud regions, ensuring low-latency access for users worldwide.


### Installation

#### Using MongoDB Atlas

1. **Create a MongoDB Atlas account**: Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) and sign up for a free account.

2. **Create a new cluster**: Follow the prompts to set up a new cluster.

3. **Whitelist your IP address**: Go to the Network Access section and add your current IP address to allow connections.

4. **Create a database user**: In the Database Access section, create a new user with the necessary permissions.

5. **Get the connection string**: Navigate to the Cluster dashboard, click on "Connect", and copy the connection string provided. Replace the username and password placeholders in the string.

6. **Update the MongoDB connection string in `python-backend.py`**:

   ```
   mongo_client = MongoClient("<your-mongodb-atlas-connection-string>")
   ```

### Clone the repository**:

   ```
   git clone <repository-url>
   cd <repository-directory>
   ```


### Build the Docker image:
```
docker build -t python-flask-app .
docker push <repo>/<image_name>
```
### Run the application locally:
```
python3 python-backend.py
```
or
```
docker run -dit -p 5000:5000 <image_name>
access the application via public ip of the server with port 5000
```
### The application will be accessible at http://localhost:5000 or if you're running in cloud server http://<public ip>:5000.

## API Endpoints

### Execute Code
### POST /execute

Submit Python code for execution.

Request Body:
```
{
  "code": "<base64-encoded-python-code>",
  "language": "python"
}
```
Response:
```
{
  "execution_id": "<unique-execution-id>",
  "message": "Job submitted for execution."
}
```

### Get Execution Result
### GET /result/<execution_id>

Retrieve the result of the executed code.

Response:
```
{
  "_id": "<mongo-document-id>",
  "execution_id": "<unique-execution-id>",
  "code": "<user-submitted-code>",
  "output": "<execution-output>",
  "status": "<success|failed>",
  "timestamp": "<execution-timestamp>"
}
```

## Dockerfile
The Dockerfile provided is used to build the Docker image for the microservice. It uses the official Python 3.9 slim image as a base, installs required dependencies, and runs the application.

### Requirements
The required packages for the application are listed in requirements.txt:
```
Flask
pymongo
pymongo[srv]
kubernetes
```

To install the requirements, run:
```
pip3 install -r requirements.txt
```

## Deployment to Kubernetes
- Deploy the Docker image to your container registry (e.g., AWS ECR, Docker Hub).

- Create a Kubernetes deployment. Ensure you have the necessary configuration to deploy the service.

- Create a Service to expose the deployment

**To expose the application using an AWS Load Balancer, create a service with the LoadBalancer type in your Kubernetes YAML configuration**

- Set up Ingress to route external traffic to the service and also to access the Application Using Custom Domain Names


## Contributing
Contributions are welcome! Please feel free to submit a pull request or open an issue if you find a bug or have a feature request.