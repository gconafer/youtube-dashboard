data "aws_ami" "amazon_linux" {
  most_recent = true
  filter {
    name = "name"
    values = [
    "amzn2-ami-hvm-2.0.*-x86_64-gp2"]
  }
  owners = [
  "amazon"]
}

data "template_file" "user_data" {
  template = file("./templates/bastion/user-data.sh.tpl")

  vars = {
    db_host = aws_db_instance.main.address
    db_name = aws_db_instance.main.name
    db_user = aws_db_instance.main.username
    db_pass = aws_db_instance.main.password
  }
}


resource "aws_iam_role" "bastion" {
  name               = "${local.prefix}-bastion"
  assume_role_policy = file("./templates/bastion/instance-profile-policy.json")

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "bastion_attach_policy1" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
  role       = aws_iam_role.bastion.name
}

resource "aws_iam_role_policy_attachment" "bastion_attach_policy2" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"
  role       = aws_iam_role.bastion.name
}

resource "aws_iam_instance_profile" "bastion" {
  name = "${local.prefix}-bastion-instance-profile"
  role = aws_iam_role.bastion.name
}

resource "aws_instance" "bastion" {
  ami                  = data.aws_ami.amazon_linux.id
  instance_type        = "t2.micro"
  user_data            = data.template_file.user_data.rendered
  iam_instance_profile = aws_iam_instance_profile.bastion.name
  key_name             = var.bastion_key_name
  subnet_id            = aws_subnet.public_a.id

  vpc_security_group_ids = [
    aws_security_group.bastion.id
  ]

  tags = merge(
    local.common_tags,
    map("Name", "${local.prefix}-bastion")
  )
}

resource "aws_security_group" "bastion" {
  description = "Control bastion inbound and outbound access"
  name        = "${local.prefix}-bastion"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port = 22
    protocol  = "tcp"
    to_port   = 22
    cidr_blocks = [
    "0.0.0.0/0"]
  }

  ingress {
    from_port = 8888
    protocol  = "tcp"
    to_port   = 8888
    cidr_blocks = [
    "0.0.0.0/0"]
  }

  egress {
    from_port = 80
    protocol  = "tcp"
    to_port   = 80
    cidr_blocks = [
    "0.0.0.0/0"]
  }

  egress {
    from_port = 443
    protocol  = "tcp"
    to_port   = 443
    cidr_blocks = [
    "0.0.0.0/0"]
  }

  egress {
    from_port = 5432
    protocol  = "tcp"
    to_port   = 5432
    cidr_blocks = [
      aws_subnet.private_a.cidr_block,
      aws_subnet.private_b.cidr_block,
    ]
  }

  tags = local.common_tags
}