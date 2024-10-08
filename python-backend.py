import logging
from flask import Flask, request, jsonify
from kubernetes import client as k8s_client, config
import base64
import uuid
import os
from pymongo import MongoClient
import datetime
import time  # Import time for sleep

app = Flask(__name__)

# Setup basic logging
logging.basicConfig(level=logging.INFO)

# MongoDB setup
#mongo_client = MongoClient("mongodb+srv://<username>:<password>@cluster0.ffokw.mongodb.net/?retryWrites=true&w=majority&appName=<clustername>")
mongo_client = MongoClient("<MONGO-CLUSTER-URL>")   # MongoDB connection URL
db = mongo_client['code_execution']     # Database for storing code executions
executions = db['executions']   # Collection for storing executions

# Ensure index on execution_id for performance
db.executions.create_index("execution_id", unique=True)

NAMESPACE = "default"  # Namespace for Kubernetes jobs

# Load Kubernetes configuration from kubeconfig file
config.load_kube_config()

# Kubernetes API clients
v1_batch_api = k8s_client.BatchV1Api()
v1_core_api = k8s_client.CoreV1Api()


# Function to create a Kubernetes job
def create_k8s_job(execution_id, user_code):
    # Security context to ensure the pod runs as a non-root user
    security_context = k8s_client.V1SecurityContext(
        run_as_non_root=True,
        run_as_user=1000,  # Example non-root user ID
        capabilities=k8s_client.V1Capabilities(drop=["ALL"])  # Drop all capabilities
    )
    
    # Define resource limits for the Kubernetes pod
    resources = k8s_client.V1ResourceRequirements(
        limits={"cpu": "500m", "memory": "256Mi"},
        requests={"cpu": "250m", "memory": "128Mi"}
    )
    
    # Define the container that will execute the user's Python code
    container = k8s_client.V1Container(
        name="user-code",
        image="python:3.9",     # Base Python 3.9 image
        command=["python", "-c", user_code],        # Execute the provided Python code
        security_context=security_context,
        resources=resources
    )
    
    # Define the Pod template for the Kubernetes job
    template = k8s_client.V1PodTemplateSpec(
        spec=k8s_client.V1PodSpec(
            containers=[container],
            restart_policy="Never"       # Job should not restart on failure
        )
    )
    
     # Define the job specification
    job_spec = k8s_client.V1JobSpec(
        template=template,
        active_deadline_seconds=600  # 10 minutes timeout
        )
    
    # Define metadata for the job, including a unique name
    job_metadata = k8s_client.V1ObjectMeta(name=f"user-code-job-{execution_id}")
    
    # Create the job definition
    job = k8s_client.V1Job(
        metadata=job_metadata,
        spec=job_spec
    )
    
    # Attempt to create the Kubernetes job
    try:
        v1_batch_api.create_namespaced_job(
            namespace=NAMESPACE,
            body=job
        )
        logging.info(f"Job {execution_id} created successfully.")
    except k8s_client.ApiException as e:
        logging.error(f"Kubernetes API error: {e}")
        raise Exception(f"Kubernetes API error: {str(e)}")


# API route to accept code execution requests
@app.route('/execute', methods=['POST'])
def execute():
    # Get JSON payload from the request
    data = request.get_json()
    encoded_code = data.get('code')     # Get base64-encoded code from the request
    language = data.get('language')     # Get the language, should be 'python'

    # Check if the language is Python, return an error if not
    if language.lower() != 'python':
        return jsonify({'error': 'Only Python language is supported'}), 400

    # Base64 decode
    try:
        user_code = base64.b64decode(encoded_code).decode('utf-8')
    except Exception as e:
        return jsonify({'error': 'Invalid base64 encoding'}), 400

    # Check if code is provided, return error if empty
    if not user_code:
        return jsonify({'error': 'No code provided'}), 400
    
    # Create a unique execution ID based on the current timestamp
    execution_id = str(datetime.datetime.utcnow().timestamp())

    # Store the code and execution metadata in MongoDB
    try:
        executions.insert_one({
            "execution_id": execution_id,
            "code": user_code,
            "output": None,     # Output will be updated later
            "timestamp": datetime.datetime.utcnow()
        })

        logging.info(f"Execution {execution_id} stored in MongoDB.")
    except pymongo.errors.PyMongoError as e:
        logging.error(f"MongoDB error: {e}")
        return jsonify({'error': 'Database error, could not save execution data'}), 500

    # Create Kubernetes Job
    try:
        create_k8s_job(execution_id, user_code)
    except k8s_client.ApiException as e:
        if e.status == 400:
            return jsonify({'error': 'Bad request to Kubernetes API'}), 400
        elif e.status == 404:
            return jsonify({'error': 'Kubernetes resource not found'}), 404
        else:
            return jsonify({'error': 'Kubernetes API error'}), 500

    return jsonify({'execution_id': execution_id, 'message': 'Job submitted successfully.'}), 200


# API route to fetch the result of an execution
@app.route('/result/<execution_id>', methods=['GET'])
def result(execution_id):
    # Retrieve execution data from MongoDB using execution_id
    execution_data = executions.find_one({'execution_id': execution_id})
    if execution_data is None:
        return jsonify({'error': 'Execution not found'}), 404

    try:
        # Get the status of the Kubernetes job
        job = v1_batch_api.read_namespaced_job(name=f"user-code-job-{execution_id}", namespace="default")

        # If the job succeeded, get the pod logs
        if job.status.succeeded:
            pods = v1_core_api.list_namespaced_pod(namespace=NAMESPACE, label_selector=f"job-name=user-code-job-{execution_id}")
            pod_name = pods.items[0].metadata.name if pods.items else None

            if pod_name:
                logs = v1_core_api.read_namespaced_pod_log(name=pod_name, namespace=NAMESPACE)
                execution_data['status'] = 'success'
                execution_data['output'] = logs
            else:
                execution_data['status'] = 'success'
                execution_data['output'] = 'No pod found for this job.'
        elif job.status.failed:
            execution_data['status'] = 'failed'
            execution_data['error'] = job.status.failed_conditions[0].reason

        execution_data['_id'] = str(execution_data['_id'])
        return jsonify(execution_data)
    except k8s_client.ApiException as e:
        return jsonify({'error': str(e)}), 500

# Route to clean up Kubernetes jobs
@app.route('/cleanup/<execution_id>', methods=['DELETE'])
def cleanup(execution_id):
    try:
        v1_batch_api.delete_namespaced_job(
            name=f"user-code-job-{execution_id}",
            namespace=NAMESPACE,
            body=k8s_client.V1DeleteOptions(propagation_policy='Foreground')
        )
        logging.info(f"Job {execution_id} cleaned up successfully.")
        return jsonify({'message': f'Job {execution_id} cleaned up.'}), 200
    except k8s_client.ApiException as e:
        logging.error(f"Error cleaning up job: {e}")
        return jsonify({'error': str(e)}), 500


# Health check route to verify the API is running
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

# Main entry point for running the Flask application
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)