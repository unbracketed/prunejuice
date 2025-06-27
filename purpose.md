# Purpose

The purpose of this project is to provide a collection shell script utilities, user manuals, project lifecycle management documentation, and workflow diagrams to help manage parallel agentic coding sessions across multiple projects. 

The working name for this project is `prunejuice`. For 

## Technology Stack

- Bash-compatible shell scripts to execute small isolated steps of managing software project lifecycles
- `gum` for scripted inputs and selections (https://github.com/charmbracelet/gum) (assumed to be available as pre-requisite)
- Git worktrees for allowing simultaneous isolated lines of development within the same repo
- tmux for managing terminal sessions for each worktree session
- Claude Code will be run in sessions to assist with technical tasks 
- mkdocs with Material theme for project documentation
- `gh` for interacting with Github (assumed to be available as pre-requisite)


## Inspiration and Philosophy

Follow closely these ideas:
https://www.pulsemcp.com/posts/how-to-use-claude-code-to-wield-coding-agent-clusters

A key section about workflow from that article:

---
You'll notice in my gw.sh file that I've introduced a notion of "MCP templates" (perhaps should be renamed to "profiles") where I've started to curate some common combinations of MCP servers I might want Claude Code to access. The way this works for me:

1. When I run pgw new-feature, I can do something like pgw new-feature -m dwh to invoke an MCP profile
2. That dwh (data warehouse) profile contains the MCP servers I might need to work with the data-heavy portion of my monorepo: BigQuery, dbt, Postgres, etc.
3. The bash script copies the .mcp.json template to be in the root folder, where it is .gitignored but active within that worktree branch
4. This means Claude Code is started with those MCP servers active
---

## Feature Items

### Central Logging

Log workflow events to a central sqlite database (location configurable)

### Configuration Profiles

Collections of Claude Code configurations and/or project settings to be copied to each worktree

### Store Claude Code Sessions with Project

Use a wrapper to launch Claude Code that will grab the session, sanitize to Markdown, and save locally to the project


## Tool Ideas

analyze issue

Repomix project

context builder

claude code wrapper





