provider "aws" {
  access_key = "${var.aws_access_key}"
  secret_key = "${var.aws_secret_key}"
  region = "ap-southeast-1"
}

resource "aws_instance" "web" {
  ami = "ami-21d30f42"          # image
  instance_type = "t2.micro"

  connection {
    user = "ubuntu"             # ssh -i *.pem ubuntu@54.254.241.192
    private_key = "${file("${var.key_path}")}"
  }

  key_name = "${var.key_name}"

  security_groups = ["${aws_security_group.webaccess.name}"]

  provisioner "remote-exec" {
    inline = [
      "sudo apt-get -y update",
      "sudo apt-get install -y nginx",
    ]
  }
}

resource "aws_security_group" "webaccess" {
  name = "zjjbye"
  description = "security group rule to allow external access to 8080"

  # - allow ssh connection
  ingress {
    from_port = 22
    to_port = 22
    protocol = "tcp"
    cidr_blocks = ["0.0.0.0/0"]   # all
  }

  # - allow http connection
  ingress {
    from_port = 80
    to_port = 80
    protocol = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port = 0
    to_port = 0
    protocol = "-1"             # all
    cidr_blocks = ["0.0.0.0/0"]
  }
}