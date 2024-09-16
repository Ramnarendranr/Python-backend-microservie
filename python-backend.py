from flask import Flask, request, jsonify
from kubernetes import client as k8s_client, config
import base64
import uuid
import os
from pymongo import MongoClient
import datetime
import time  # Import time for sleep

app = Flask(__name__)

mongo_client = MongoClient("mongodb+srv://neranpolo99:2HDB8C8vIF0M2AE0@cluster0.ffokw.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = mongo_client['code_execution']
executions = db['executions']

NAMESPACE = "default"  # Namespace for Kubernetes jobs

config.load_kube_config()
v1_batch_api = k8s_client.BatchV1Api()
v1_core_api = k8s_client.CoreV1Api()

@app.route('/execute', methods=['POST'])
def execute():
    data = request.get_json()
    encoded_code = data.get('code')
    language = data['language']

    # Base64 decode
    user_code = base64.b64decode(encoded_code).decode('utf-8')
    execution_id = str(uuid.uuid4())

    # Store the code and execution metadata in MongoDB
    executions.insert_one({
        "execution_id": execution_id,
        "code": user_code,
        "output": None,
        "timestamp": datetime.datetime.utcnow()
    })

    # Create Kubernetes Job
    #create_k8s_job(execution_id, decoded_code)
    '''job_yaml = f"""
    apiVersion: batch/v1
    kind: Job
    metadata:
      name: user-code-job-{execution_id}
    spec:
      template:
        spec:
          containers:
          - name: user_code
            image: python:3.9
            command: ["python", "-c", user_code]
          restartPolicy: Never
    """
'''
    try:
        v1_batch_api = k8s_client.BatchV1Api()
        v1_batch_api.create_namespaced_job(
            namespace=NAMESPACE,
            body=k8s_client.V1Job(
                metadata=k8s_client.V1ObjectMeta(
                    name=f"user-code-job-{execution_id}"), 
                spec=k8s_client.V1JobSpec(
                    template=k8s_client.V1PodTemplateSpec(
                        spec=k8s_client.V1PodSpec(
                            containers=[k8s_client.V1Container(name="user-code", image="864406680995.dkr.ecr.us-east-1.amazonaws.com/python-flask-app-repo:latest", command=["python", "-c", user_code])],
                            restart_policy="Never"
                            )
                        )
                    )
                )
            )
        #job_results[execution_id] = {'status': 'running'}
        return jsonify({'execution_id': execution_id, 'message': "Job submitted for execution."}), 202
    except K8s_client.ApiException as e:
        return jsonify({'error': str(e)}), 500

@app.route('/result/<execution_id>', methods=['GET'])
def result(execution_id):
    execution_data = executions.find_one({'execution_id': execution_id})
    if execution_data is None:
        return jsonify({'error': 'Execution not found'}), 404

    try:
        job = v1_batch_api.read_namespaced_job(name=f"user-code-job-{execution_id}", namespace="default")
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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
