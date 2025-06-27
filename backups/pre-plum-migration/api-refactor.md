
## Tools

`plum` - Manages Git worktrees for each project
`pots` - Manager Tmux sessions for each project worktree
`prunejuice` - Coordinate project lifecycle steps with coding agents

### Plum

Manages Git worktrees for a project, allowing units of work to be done in isolation and in parallel with other work. Configurable options for location, naming and behavior of worktrees. 

This tool can be useful on its own but is intended as a utility supporting `prunejuice`
### Pots

A worktree-aware tmux session manager, allowing unit of work processes to run in the background. Each worktree can have one or more named sessions associated, with names referencing the project and worktree for easy global session management.  Having work run in tmux sessions allows for all the benefits of remote access and "in-and-out" session management that works well for tending parallel lines of work.

### Prunejuice

Provides commands for executing project lifecycle steps in tandem with coding agents. This is the primary command users will interface with; users are encouraged to adopt the alias `prj` as a shorthand (kind of like "project"), or even `pj`.  

The philosophy:

- Make each step of the SDLC scriptable or able to run in a pipeline independently
- Generate and store supporting artifacts with each step (plans, specs, analysis, reviews, summaries)
- Prompts and instructions should be first class items and be represented as template files in the project
- Prefer to run Claude Code (`claude`) in non-interactive, dangerous mode; the role of `prunejuice` commands is to use the SDLC Command definitions to assemble the full prompt and context to pipe into Claude Code. 
- A command will follow these steps:
	1. Assemble context: command prompt template + tool instructions
	2. Store the requested prompt containing all the details to have Claude Code work on
	3. Open a worktree session and 
	4. Write the resulting response to a document
- Ability to launch an MCP server for the project providing the commands as tools

## Projects

A project is a directory where stuff gets built, researched, or analyzed. A project directory is assumed to also represent a Git repository. Projects rely on Git worktrees to organize units of work, which are typically steps or tasks within a software development lifecycle (SDLC)

Since each team and every solo developer might have their own ideas about how to operate development processes, the tool allows for commands and flows to determined by definition files. An opinionated set of defaults are provided to help get started with. 

Users of `prunejuice` will be using a combination of commands to help manage project work: planning, researching, implementation, reviews, analysis, etc. The exact set of commands available will depend on your settings.

### Layout

Projects will use a few directories for managing SDLC actions and output artifacts. 

`/specs` - each task will have a named directory containing documents used to coordinate work: specs, analysis, summaries, research. Example:
- `/specs/45-login-form-error/implementation-plan.md`
`/specs/<task-dir>/.agent-sessions` - stores formatted log files of Claude Code sessions

### Events

Command runs will be recorded in a sqlite database.

### SDLC Commands

A `prunejuice` SDLC command handles a unit of project work. Each command is defined in a file with metadata and the steps to run. Each team, developer, and/or project may want to customize the command definitions to fit desired conventions. These files live with the repository so they can be edited, referenced, and versions.

**Command Properties**
- **name** - how the command will be referenced on the command line. Example: `prj analyze-issue`
- base - Base Command to inherit from (default: `BASE-COMMAND`)
- desc -
- **arguments**
- **prompt file**
- **steps** - a list of steps to execute to complete the unit of work
- context - a list of scripts to run or documents to include for the prompt context
- tools
- script

The minimum properties for a SDLC Command are: `name`, `arguments`, `prompt-template`

**Command Definition Example**
```yaml
name: analyze-issue
base: BASE-COMMAND
desc: Analyze a Github Issue and make a plan to implement or resolve
prompt-template: .prj/sdlc/commands/analyze-issue.md
steps:
  - context: analyze-issue-template
  - context: read-gh-issue
  - context: tool notes
  - store-prompt-request
  - prompt-agent
  - write-implementation-plan
  - store-session
tools:
  - PROJECT_TOOLS
  - another-mcp-good-for-this-command
```

#### Defining Commands

##### steps
A list of script names or commands to run sequentially
##### base
Refers to the Base Command to inherit from (default: BASE-COMMAND). Multiple Base Commands can be used to organize common steps and settings for groups of related commands.

#### Base Commands

One or more Base Commands can be defined from which the SDLC commands will inherit properties and steps. Base Commands are not run directly; they act as templates to capture common steps and settings for multiple SDLC commands.

**Base Command Definition**
```yaml
name: BASE-COMMAND
desc: The primary Base Command
steps:
  - new worktree
  - new tmux session
  - init session prompt file
  - log project event started
  - build context
  - $COMMAND-STEPS
  - store claude session
  - log project event completed
tools:
  - MCP:
    - zen
    - context7
```


## SDLC Command Sets

A goal of `prunejuice` is to provide comprehensive commands for managing SDLC steps. Since each organization, team, and/or developer may have their own preferred SDLC methodology and terminology, `prunejuice` provides a flexible system for defining the sets of commands that match your needs best.

However you prefer to mix and match the concepts of Milestone, Epic, Sprint, Task, Feature, Fix, Change Request, etc. can be accommodated via the SDLC Command Set
support PLC command sets for different preferences of project org and terminology:
milestones, epics, sprints, feature, bugfix, etc.

SDLC Command Set
- Which steps and their names
- How artifact docs are named
- Where to store artifact documents



**SDLC command sets can be defined like**
```yaml
philosophy: Milestone, Sprint, Task
hierarchy:
- Milestone
	name: milestone
	artifacts: specs/milestones
- Sprint
    name: sprint
    artifacts: specs/sprints
- Task
    name: task
    artifacts: specs/tasks
    types:
      - bugfix
      - task
      - research
      - debug
```

## Tools

- Bash-compatible scripts for defining utils and commands
- Python scripts are a good choice too, especially with `uvx` and PEP723
- `gum` from https://charm.sh for adding nice selection and input widgets
- `gh` for interfacing with Github
- Repomix https://github.com/yamadashy/repomix - help with context packing for some tasks to add parts or all of the project code in the prompt
- tmux for session management
- mkdocs with Material theme for project docs

## Roadmap

### Provide some default SDLC Commands and Command Sets

Example:

> The server exposes 22 MCP tools across 6 handler modules for comprehensive lifecycle management:

- Requirement Management
- Task Management
- Architecture Management
- Project Monitoring
- Documentation Export Tools
- Interactive Interview Tools

### Use Git Trailers to add additional commit context

Ideas:
- token counts used
- duration
- tools used summary
