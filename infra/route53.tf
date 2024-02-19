# data "aws_ssm_parameter" "base_domain" {
#   name = "/environment/base_domain"
# }

# data "aws_route53_zone" "base_domain" {
#   name = data.aws_ssm_parameter.base_domain.value
# }

# resource "aws_ses_domain_identity" "base_domain" {
#   domain = data.aws_ssm_parameter.base_domain.value
# }

# resource "aws_route53_record" "amazonses_verification_record" {
#   zone_id = data.aws_route53_zone.base_domain.zone_id
#   name    = "_amazonses.${aws_ses_domain_identity.base_domain.id}"
#   type    = "TXT"
#   ttl     = "600"
#   records = [aws_ses_domain_identity.base_domain.verification_token]
# }

# resource "aws_ses_domain_identity_verification" "verification" {
#   domain = aws_ses_domain_identity.base_domain.id

#   depends_on = [aws_route53_record.amazonses_verification_record]
# }
