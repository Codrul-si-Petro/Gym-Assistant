# dbt Transformation: Dependency Chain & Build Order

This project uses **tags** to run the pipeline in two phases: seeds first (load + test), then models (build + test). That way seed data is validated before any models are built.

# Build command (two-phase)

Run seeds and their tests first, then models and their tests:

### dbt build -s tag:seeds && dbt build -s tag:models

## Dependency chain

### Phase 1: Seeds (`tag:seeds`)

Seeds are CSV files loaded into the `staging` schema. They have no dependencies on each other.


Tests on seeds (e.g. `not_null`, `unique`, `relationships` between seeds, and source `fact_workouts` → seeds) run in this phase. If any seed or seed test fails, the run stops and models are not built.

### Phase 2: Models (`tag:models`)

Models are tables which live in the `core` schema and depend on seeds (and sometimes other models). 


# Viewing dependency graphs with dbt docs

dbt ships with a docs site that includes an interactive **Lineage** (dependency) graph. You can see how seeds, models, sources, and tests connect.

## One-time setup

None. Use your existing `dbt_project.yml` and `profiles.yml`. The docs are generated from your project and (optionally) from the database.

## Generate and open the docs

### 1. Generate the manifest and catalog

From the project root (the directory that contains `dbt_project.yml`):

dbt docs generate

dbt docs serve

## Resources:
- Learn more about dbt [in the docs](https://docs.getdbt.com/docs/introduction)
- Check out [Discourse](https://discourse.getdbt.com/) for commonly asked questions and answers
- Join the [chat](https://community.getdbt.com/) on Slack for live discussions and support
- Find [dbt events](https://events.getdbt.com) near you
- Check out [the blog](https://blog.getdbt.com/) for the latest news on dbt's development and best practices
