# Shared helpers for analysis entrypoints. Sourced with CWD at the repo root.
suppressPackageStartupMessages(library(DBI))

`%||%` <- function(a, b) if (is.null(a) || length(a) == 0) b else a

# Choose the data backend from the environment:
#   - in AoU (WORKSPACE_CDR set): BigQuery over the real CDR
#   - locally: DuckDB over the Eunomia synthetic dataset
# Both return a DBI connection, so the same SQL runs against either.
pick_connection <- function() {
  cdr <- Sys.getenv("WORKSPACE_CDR", "")
  if (nzchar(cdr)) {
    suppressPackageStartupMessages(library(bigrquery))
    parts <- strsplit(cdr, "\\.")[[1]]
    DBI::dbConnect(
      bigrquery::bigquery(),
      project = parts[1], dataset = parts[2],
      billing = Sys.getenv("GOOGLE_CLOUD_PROJECT")
    )
  } else {
    suppressPackageStartupMessages(library(duckdb))
    DBI::dbConnect(duckdb::duckdb(), dbdir = "data/eunomia.duckdb", read_only = TRUE)
  }
}

# SHA-256 truncated — fallback only, for the rare case an id must be named in
# output. Row-level output should not cross the air-gap at all.
hash_id <- function(x) {
  suppressPackageStartupMessages(library(digest))
  substr(digest::digest(as.character(x), algo = "sha256"), 1, 12)
}
