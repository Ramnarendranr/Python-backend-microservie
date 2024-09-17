provider "aws"{
    region = "us-east-1"
}

resource "aws_s3_bucket" "terraform-backend" {
  bucket = "eks-cluster-remote-backend-python-microservice-app"
}

resource "aws_dynamodb_table" "terraform-lock" {
  name = "terraform-lock"
  billing_mode = "PAY_PER_REQUEST"
  hash_key = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }
}
