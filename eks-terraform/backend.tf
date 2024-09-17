terraform {
  backend "s3" {
    bucket = "eks-cluster-remote-backend-python-microservice-app"
    region = "us-east-1"
    key = "python-microservice-flask-app/terraform.tfstate"
    dynamodb_table = "terraform-lock"
  }
}