# Curriculum Design Algorithm

How to analyze any codebase (or a specific part of one) and produce an ordered
lesson plan.

## Scope

The user may request a walkthrough of:
- The entire codebase (default)
- A specific directory, module, or subsystem (e.g. "walk me through the
  pipeline module" or "explain src/auth/")
- A specific concern (e.g. "walk me through how authentication works")

When scoped to a subset, apply the same algorithm but only to files within
scope. Still trace dependencies outside scope to note them as "external to
this walkthrough" in lesson openings.

## Phase 1: Discovery

### Detect Project Type

Read configuration files to determine language and framework:

| File | Indicates |
|------|-----------|
| package.json | Node.js / TypeScript |
| pyproject.toml, setup.py | Python |
| Cargo.toml | Rust |
| go.mod | Go |
| pom.xml, build.gradle | Java / Kotlin |
| Makefile, CMakeLists.txt | C / C++ |
| mix.exs | Elixir |
| Gemfile | Ruby |
| DESCRIPTION, NAMESPACE | R package |
| renv.lock, .Rproj | R project |

If multiple indicators exist, identify the primary language by source file
count.

### Map Source Files

Use Glob to find all source files. Exclude:
- node_modules, vendor, .venv, __pycache__, target, build, dist, renv/library
- Generated files (*.generated.*, *.pb.go, etc.)
- Boilerplate config (tsconfig, eslint, prettier, etc.)

Group files by directory — each top-level source directory typically represents
a module or domain boundary.

### Trace Dependencies

For each source file, Grep for import statements. Build an adjacency list of
**internal** dependencies only (ignore external packages).

Language-specific patterns:

| Language | Import pattern |
|----------|---------------|
| Python | `from X import`, `import X` |
| TypeScript/JS | `import ... from`, `require(...)` |
| Rust | `use crate::`, `mod ` |
| Go | `import "project/..."` |
| Java/Kotlin | `import com.project...` |
| R | `source("...")`, `box::use(...)`, internal `NAMESPACE` imports |

## Phase 2: Ordering

### Topological Sort with Grouping

1. Build the dependency graph from Phase 1.
2. Identify leaf nodes (modules with no internal imports) — these are
   foundational and should come first.
3. Topological sort. When multiple modules have no ordering constraint,
   group by functional relatedness.
4. Place entry point / orchestration layer last — it ties everything together.

### Recommended Order Template

Most codebases map to this progression:

1. **Orientation** — README, project structure, config, how to run it.
   Always first.
2. **Tests overview** — Scan test directory early. Test names and structure
   reveal project goals, expected behaviors, and edge cases before diving
   into implementation. Keep this lighter than implementation lessons —
   focus on what the tests tell you about intent, not test mechanics.
3. **Data layer** — Models, types, schemas, database access. The nouns.
4. **Core logic** — Business rules, algorithms, transformations. The verbs.
5. **Integration layer** — External APIs, file I/O, network calls.
6. **Orchestration** — Entry points, CLI, routers, pipelines that wire
   everything together.
7. **UI / presentation** (if applicable) — Frontend components, templates.

Not every codebase has all layers. Skip what doesn't apply. Add layers if
the codebase has additional concerns (e.g. middleware, plugins, migrations).

### Handling Large Codebases (50+ source files)

Add a preliminary "Architecture Overview" lesson after orientation. This
lesson presents:
- High-level module map (which directories do what)
- Main data flow through the system
- Key design patterns in use

Then group related modules into thematic lessons rather than
one-file-per-lesson.

### Handling Monorepos

1. Start with shared/common packages
2. Ask the user which service to focus on
3. Generate a sub-curriculum for that service
4. Offer to continue to other services afterward

## Phase 3: Lesson Content Planning

For each lesson, identify:

- **Files**: The files that will be read and discussed
- **Concepts**: Key ideas the user should take away
- **Prerequisites**: Which earlier lessons must be understood first
- **Complexity**: Low / Medium / High

Complexity guide:
- **Low**: Straightforward CRUD, simple data models, configuration
- **Medium**: Business logic with branching, moderate abstraction
- **High**: Complex algorithms, advanced patterns, concurrency

For High-complexity lessons, consider splitting into sub-lessons.

Defer detailed **task** breakdown (specific functions, code blocks) until the
lesson is actually being delivered — this keeps the curriculum lightweight and
allows it to adapt to what the code actually contains at read time.
