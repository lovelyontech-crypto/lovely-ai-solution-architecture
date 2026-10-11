variable "github_owner" {
  description = "GitHub user or organisation that owns the private repository (OD-28)"
  type        = string
}

variable "repository_name" {
  description = "Name of the private platform repository"
  type        = string
  default     = "bharat-equity-intelligence"
}

variable "required_reviewers" {
  description = "Approving reviews required on main"
  type        = number
  default     = 1
}

variable "engineering_owner" {
  description = "GitHub handle or team for workflows and config, e.g. @org/engineering"
  type        = string
}

variable "quant_owner" {
  description = "GitHub handle or team that approves model registry changes"
  type        = string
}

variable "compliance_owner" {
  description = "GitHub handle or team that approves prompts, disclosures and recipient config"
  type        = string
}

variable "actions_variables" {
  description = "Non-secret Actions variables (vars.*). Never put credentials or email addresses here. Add UPSTOX_TOKEN_ISSUED_ON = \"YYYY-MM-DD\" once the Analytics Token is generated."
  type        = map(string)
  default = {
    PLATFORM_UNIVERSE      = "NIFTY100"    SCHEDULE_TOLERANCE_MIN = "30"
    REPORT_FORMAT_DEFAULT  = "html_csv"
    LLM_DAILY_TOKEN_CAP    = "200000"
  }
}
