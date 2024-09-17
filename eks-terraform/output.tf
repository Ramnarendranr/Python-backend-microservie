output "cluster_id" {
  value = aws_eks_cluster.python_flask_app.id
}

output "node_group_id" {
  value = aws_eks_node_group.python_flask_app.id
}

output "vpc_id" {
  value = aws_vpc.python_flask_app_vpc.id
}

output "subnet_ids" {
  value = aws_subnet.python_flask_app_subnet[*].id
}