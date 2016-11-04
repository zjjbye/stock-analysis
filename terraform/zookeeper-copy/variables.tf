variable "aws_region" {
  default = "ap-southeast-1"
}

variable "availiability_zones" {
  default = "ap-southeast-1a,ap-southeast-1b"
}

variable "aws_amis" {
  type = "map"
  default = {
    "ap-southeast-1" = "ami-a1288ec2"
    "us-east-1" = "ami-40d28157"
  }
}

variable "aws_access_key" {
  default = ""
}

variable "aws_secret_key" {
  default = ""
}

variable "key_name" {
  description = "Name of your AWS key pair"
  default = ""
}

variable "key_path" {
  description = "path to your private key file"
  default = "../../cred/xxx.pem"
}

variable "zookeeper_count" {
  default = 1
}

variable "zookeeper_aws_amis" {
  type = "map"
  default = {
    "ap-southeast-1" = "ami-a1288ec2"
    "us-east-1" = "ami-40d28157"
  }
}

variable "kafka_count" {
  default = 1
}

variable "kafka_aws_amis" {
  type = "map"
  default = {
    "ap-southeast-1" = "ami-a1288ec2"
    "us-east-1" = "ami-40d28157"
  }
}

variable "instance_type" {
  default = "t2.medium"
}