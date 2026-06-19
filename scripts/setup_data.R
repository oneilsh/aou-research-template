#!/usr/bin/env Rscript
# Fetch the OHDSI Eunomia synthetic OMOP dataset and persist it as a DuckDB
# file at data/eunomia.duckdb. Nothing licensed is committed — each user pulls
# OHDSI's public, Apache-2.0 dataset. data/ is gitignored.
#
# VERIFY: the exact Eunomia API differs across versions. This targets Eunomia
# 2.x (DuckDB backend). If the call below errors, check
# `?Eunomia::getEunomiaConnectionDetails` for your installed version.
#
# API NOTE (installed Eunomia 2.1.0): getEunomiaConnectionDetails() defaults to
# SQLite and does not accept a databaseFile path directly for DuckDB output.
# Instead, getDatabaseFile("GiBleed", dbms="duckdb", databaseFile=out) is used,
# which downloads the GiBleed synthetic CDM and writes a DuckDB file at `out`.
suppressPackageStartupMessages({ library(DBI); library(duckdb); library(Eunomia) })

dir.create("data", showWarnings = FALSE)
out <- "data/eunomia.duckdb"

# getDatabaseFile builds (or downloads then builds) a DuckDB-backed synthetic
# CDM at the given path. "GiBleed" is the default Eunomia dataset.
# (Eunomia 2.x: use getDatabaseFile instead of getEunomiaConnectionDetails,
#  which targets SQLite only in this version.)
db_path <- Eunomia::getDatabaseFile("GiBleed", dbms = "duckdb", databaseFile = out,
                                    overwrite = TRUE)
message("Wrote ", db_path)

# Sanity check: confirm core OMOP tables are present.
con <- DBI::dbConnect(duckdb::duckdb(), dbdir = out, read_only = TRUE)
tbls <- tolower(DBI::dbListTables(con))
DBI::dbDisconnect(con, shutdown = TRUE)
stopifnot(all(c("person", "condition_occurrence") %in% tbls))
message("OK: person + condition_occurrence present.")
