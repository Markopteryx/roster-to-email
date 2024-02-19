data "aws_ssm_parameter" "to_email" {
  name            = "/lambda/env/TO_EMAIL"
  with_decryption = true
}

data "aws_ssm_parameter" "from_email" {
  name            = "/lambda/env/FROM_EMAIL"
  with_decryption = true
}

data "aws_ssm_parameter" "roster_website" {
  name            = "/lambda/env/ROSTER_WEBSITE"
  with_decryption = true
}

data "aws_ssm_parameter" "roster_username" {
  name            = "/lambda/env/ROSTER_USERNAME"
  with_decryption = true
}

data "aws_ssm_parameter" "roster_password" {
  name            = "/lambda/env/ROSTER_PASSWORD"
  with_decryption = true
}
