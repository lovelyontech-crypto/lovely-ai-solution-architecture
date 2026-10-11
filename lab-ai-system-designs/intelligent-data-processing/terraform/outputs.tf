output "repository_full_name" {
  value = github_repository.platform.full_name
}

output "repository_ssh_url" {
  value = github_repository.platform.ssh_clone_url
}

output "next_steps" {
  value = <<-EOT
    1. Run ./bootstrap.sh <owner>/<repo> to create the orphan `data` branch.
    2. Set secrets with gh secret set: UPSTOX_ANALYTICS_TOKEN, MOSPI_USERNAME, MOSPI_PASSWORD,
       LLM_API_KEY, GMAIL_SENDER, GMAIL_APP_PASSWORD, REPORT_RECIPIENT
       (MARKET_DATA_API_KEY, FUNDAMENTALS_API_KEY once the licensed vendor is chosen, OD-02).
       Set the variable UPSTOX_TOKEN_ISSUED_ON to the token's generation date.
    3. Copy ../pipelines/*.yml to .github/workflows/ and pin actions to commit SHAs.
  EOT
}
