# Repository-as-code for the Bharat Equity Intelligence Platform (BRD v1.0).
#
# Scope: GitHub settings ONLY (private repository, branch protection, Actions variables).
# This creates no cloud resources: the BRD forbids a cloud account and always-on servers (§5.5).
#
# Secrets (API keys, Gmail App Password, REPORT_RECIPIENT) are deliberately NOT managed here,
# because Terraform state would store their plaintext values. Set them with the GitHub CLI:
#   gh secret set MARKET_DATA_API_KEY --repo <owner>/<repo>
# The orphan `data` branch is created once by bootstrap.sh (Terraform cannot create orphan branches).

terraform {
  required_version = ">= 1.6"
  required_providers {
    github = {
      source  = "integrations/github"
      version = "~> 6.0"
    }
  }
}

provider "github" {
  owner = var.github_owner
  # Authenticates with the GITHUB_TOKEN environment variable (fine-grained PAT, admin on this repo only).
}

resource "github_repository" "platform" {
  name        = var.repository_name
  description = "Bharat Equity Intelligence Platform: research pipeline (private, licensed data)"
  visibility  = "private" # A-09 / OD-23: licensed data must never be public
  auto_init   = true      # creates main so CODEOWNERS and protection can be applied

  has_issues   = true
  has_wiki     = false
  has_projects = false

  allow_merge_commit     = false
  allow_squash_merge     = true
  allow_rebase_merge     = false
  delete_branch_on_merge = true
  vulnerability_alerts   = true # Dependabot alerts (§15.7 Scanning)

  security_and_analysis {
    secret_scanning {
      status = "enabled"
    }
    secret_scanning_push_protection {
      status = "enabled"
    }
  }
}

# main: code and workflows; changes only by reviewed PR (FR-175, §15.7)
resource "github_branch_protection" "main" {
  repository_id                   = github_repository.platform.node_id
  pattern                         = "main"
  enforce_admins                  = true
  require_signed_commits          = false
  required_linear_history         = true
  require_conversation_resolution = true

  required_pull_request_reviews {
    required_approving_review_count = var.required_reviewers
    require_code_owner_reviews      = true # CODEOWNERS covers workflows, models/, prompts/
    dismiss_stale_reviews           = true
  }

  required_status_checks {
    strict   = true
    contexts = ["test"] # job name in ci.yml
  }

  # CODEOWNERS is committed directly to main, so protect main only afterwards.
  depends_on = [github_repository_file.codeowners]
}

# data: written only by the workflow token; no force pushes or deletion (FR-156, §14.4.9)
resource "github_branch_protection" "data" {
  repository_id       = github_repository.platform.node_id
  pattern             = "data"
  enforce_admins      = false # workflow pushes as github-actions; humans restore via backup tags
  allows_force_pushes = false
  allows_deletions    = false
}

# Non-secret configuration exposed to workflows as `vars.*`
resource "github_actions_variable" "config" {
  for_each      = var.actions_variables
  repository    = github_repository.platform.name
  variable_name = each.key
  value         = each.value
}

resource "github_repository_file" "codeowners" {
  repository          = github_repository.platform.name
  branch              = "main"
  file                = ".github/CODEOWNERS"
  commit_message      = "chore: CODEOWNERS for workflows, models and prompts"
  overwrite_on_create = true
  content             = <<-EOT
    /.github/workflows/  ${var.engineering_owner}
    /models/             ${var.quant_owner}
    /prompts/            ${var.quant_owner} ${var.compliance_owner}
    /config/             ${var.engineering_owner} ${var.compliance_owner}
  EOT
}
