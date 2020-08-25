variable "prefix" {
  default = "collab"
}

variable "project" {
  default = "music-dashboard"
}

variable "contact" {
  default = "taejun@collabasia.co"
}

variable "db_username" {
  description = "Username for the RDS Postgres instance"
}

variable "db_password" {
  description = "Password for the RDS Postgres instance"
}

variable "bastion_key_name" {
  default = "music-dashboard-bastion"
}

variable "ecr_image_api" {
  description = "ECR image for API"
  default     = "876150697428.dkr.ecr.ap-northeast-2.amazonaws.com/music-dashboard-devops:latest"
}

variable "ecr_image_proxy" {
  description = "ECR image for Proxy"
  default     = "876150697428.dkr.ecr.ap-northeast-2.amazonaws.com/music-dashboard-proxy:latest"
}

variable "django_secret_key" {
  description = "Django Secret Key"
}

variable "private_key_id" {
  description = "Service Account private key id"
}

variable "private_key" {
  description = "Service Account private key"
}

variable "notebook_pw" {
  description = "Jupyter Notebook Password"
}