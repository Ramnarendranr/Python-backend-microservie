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
- Access to a Kubernetes cluster.
- MongoDB instance (either local or cloud-based).
- Required Python packages listed in `requirements.txt`.

### Installation

1. **Clone the repository**:

   ```bash
   git clone <repository-url>
   cd <repository-directory>


## Set up the MongoDB connection:

### Update the MongoDB connection string in python-backend.py:
```
mongo_client = MongoClient("<your-mongodb-connection-string>")
```
### Build the Docker image:

bash
Copy code
docker build -t python-flask-app .
Run the application locally (optional):

bash
Copy code
python python-backend.py
The application will be accessible at http://localhost:5000.