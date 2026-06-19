#!/usr/bin/env Rscript
# Demo entrypoint. Invoked by the runner as:
#   Rscript experiments/0001-demo/demo_effect.R --config experiments/0001-demo/runs/config.yaml
# Row-level query results stay in this process; only aggregates are printed,
# so the scrubbed summary.md carries nothing patient-level.
suppressPackageStartupMessages({ library(DBI); library(yaml) })
source("framework/shared/utilities.R")

args <- commandArgs(trailingOnly = TRUE)
cfg_path <- args[which(args == "--config") + 1]
cfg <- yaml::read_yaml(cfg_path)

con <- pick_connection()
on.exit(try(DBI::dbDisconnect(con, shutdown = TRUE), silent = TRUE), add = TRUE)

sql <- paste(readLines(cfg$sql_file), collapse = "\n")
dat <- DBI::dbGetQuery(con, sql)            # row-level; stays in memory

res <- t.test(n_conditions ~ grp, data = dat)
grp_means <- tapply(dat$n_conditions, dat$grp, mean)
cat(sprintf("[demo] group sizes: %s\n",
            paste(names(table(dat$grp)), table(dat$grp), sep="=", collapse=" ")))
cat(sprintf("[demo] mean(n_conditions): %s\n",
            paste(names(grp_means), round(grp_means, 2), sep="=", collapse=" ")))
cat(sprintf("[demo] Welch t = %.3f, df = %.1f, p = %.4g\n",
            res$statistic, res$parameter, res$p.value))
cat(sprintf("[demo] 95%% CI of mean difference: [%.3f, %.3f]\n",
            res$conf.int[1], res$conf.int[2]))

# Aggregate-only plot: group means +/- standard error. No per-person marks.
out_dir <- cfg$out_dir %||% "experiments/0001-demo/runs"
dir.create(out_dir, showWarnings = FALSE, recursive = TRUE)
ses <- tapply(dat$n_conditions, dat$grp, function(v) sd(v) / sqrt(length(v)))
png(file.path(out_dir, "demo_effect.png"), width = 600, height = 400)
bp <- barplot(grp_means, ylim = c(0, max(grp_means + 2 * ses)),
              ylab = "mean condition count",
              main = "Mean conditions by group (aggregate)")
arrows(bp, grp_means - ses, bp, grp_means + ses, angle = 90, code = 3, length = 0.05)
invisible(dev.off())
cat(sprintf("[demo] wrote aggregate plot to %s\n", file.path(out_dir, "demo_effect.png")))
