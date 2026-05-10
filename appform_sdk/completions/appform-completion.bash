# bash completion for appform SDK
# Install: source appform-completion.bash or copy to ~/.bash_completion
# Or: appform --generate-completion bash > /etc/bash_completion.d/appform

_appform_commands() {
    local cmds=(
        "config:Manage configuration"
        "extension:Manage extensions"
        "endpoint:Manage endpoints"
        "auth:Authentication operations"
        "jobs:Job operations"
        "sessions:Session operations"
        "files:File operations"
        "apps:Application operations"
        "departments:Department operations"
        "users:User operations"
    )
    COMPREPLY=( $(compgen -W "${cmds[*]}" -- "${cur}") )
    return 0
}

_appform_config_subcommands() {
    local cmds=("set:Set configuration values" "show:Show current configuration")
    COMPREPLY=( $(compgen -W "${cmds[*]}" -- "${cur}") )
    return 0
}

_appform_extension_subcommands() {
    local cmds=("list:List loaded extensions" "load:Load an extension")
    COMPREPLY=( $(compgen -W "${cmds[*]}" -- "${cur}") )
    return 0
}

_appform_endpoint_subcommands() {
    local cmds=("list:List registered endpoints" "call:Call an endpoint by name")
    COMPREPLY=( $(compgen -W "${cmds[*]}" -- "${cur}") )
    return 0
}

_appform_auth_subcommands() {
    local cmds=("login:Login with username and password" "ping:Test authentication" "logout:Logout")
    COMPREPLY=( $(compgen -W "${cmds[*]}" -- "${cur}") )
    return 0
}

_appform_jobs_subcommands() {
    local cmds=(
        "apps:List applications"
        "params:Show application parameters"
        "submit:Submit a job"
        "submit-raw:Submit a job with raw JSON"
        "list:List jobs"
        "status:List jobs by status"
        "get:Get job details"
        "stop:Stop a job"
        "suspend:Suspend a job"
        "resume:Resume a job"
        "output:Get job output"
        "files:Get job files"
        "history:Get job history"
        "history-page:List history with pagination"
        "delete:Delete a job"
        "form:Get job submission form"
        "tooltip:Get job monitoring info"
    )
    COMPREPLY=( $(compgen -W "${cmds[*]}" -- "${cur}") )
    return 0
}

_appform_sessions_subcommands() {
    local cmds=(
        "start:Start a new session"
        "list:Query sessions"
        "list-all:List all sessions"
        "connect:Get session connection info"
        "connect-launch:Connect and auto-launch client"
        "disconnect:Disconnect a session"
        "close:Close a session"
        "share:Share a session"
    )
    COMPREPLY=( $(compgen -W "${cmds[*]}" -- "${cur}") )
    return 0
}

_appform_files_subcommands() {
    local cmds=(
        "ls:List remote directory"
        "cp:Copy remote file"
        "mv:Move/rename remote file"
        "rm:Delete remote file"
        "mkdir:Create remote directory"
        "put:Upload local file to remote"
        "get:Download remote file to local"
        "compress:Compress remote directory"
        "uncompress:Uncompress remote archive"
        "conf:File confidentiality operations"
    )
    COMPREPLY=( $(compgen -W "${cmds[*]}" -- "${cur}") )
    return 0
}

_appform_apps_subcommands() {
    local cmds=("list:List all applications" "list-v2:List available apps v2")
    COMPREPLY=( $(compgen -W "${cmds[*]}" -- "${cur}") )
    return 0
}

_appform_departments_subcommands() {
    local cmds=(
        "list:List departments"
        "create:Create department"
        "update:Update department"
        "delete:Delete department"
    )
    COMPREPLY=( $(compgen -W "${cmds[*]}" -- "${cur}") )
    return 0
}

_appform_users_subcommands() {
    local cmds=(
        "list:List users"
        "create:Create user"
        "update:Update user"
        "delete:Delete user"
        "reset-password:Reset user password"
    )
    COMPREPLY=( $(compgen -W "${cmds[*]}" -- "${cur}") )
    return 0
}

_appform_global_options() {
    local opts=(
        "--base-url" "--access-key" "--access-key-secret"
        "--username" "--password" "--token"
        "--api-version" "--extensions-dir" "--config"
        "--env" "--output" "--output-template" "--profile-config"
        "--version"
        "-o"
    )
    COMPREPLY=( $(compgen -W "${opts[*]}" -- "${cur}") )
    return 0
}

_appform_output_formats() {
    local fmts=("json" "raw" "table" "text")
    COMPREPLY=( $(compgen -W "${fmts[*]}" -- "${cur}") )
    return 0
}

_appform_job_statuses() {
    local statuses=("RUN" "PEND" "DONE" "EXIT")
    COMPREPLY=( $(compgen -W "${statuses[*]}" -- "${cur}") )
    return 0
}

_appform() {
    local cur prev words cword
    _init_completion || return

    # Reset state for programmatic use
    if [[ "${COMP_LINE}" == "" && "${cur}" != "" ]]; then
        # Called from --generate-completion
        return
    fi

    case "${prev}" in
        --output|-o)
            _appform_output_formats; return
            ;;
        --base-url|--access-key|--access-key-secret|--username|--password|--token)
        --api-version|--extensions-dir|--config|--env|--output-template|--profile-config)
            return 0
            ;;
        --status)
            _appform_job_statuses; return
            ;;
    esac

    # Parse command path
    local cmd="" cmd2=""
    local i
    for ((i=1; i<cword; i++)); do
        case "${words[i]}" in
            --*) ;;
            -*)
                if [[ ${#words[i]} -eq 1 ]] || [[ ${words[i]} == -*=* ]]; then
                    ;;
                else
                    continue
                fi
                ;;
            *)
                if [[ -z "${cmd}" ]]; then
                    cmd="${words[i]}"
                elif [[ -z "${cmd2}" ]]; then
                    cmd2="${words[i]}"
                fi
                ;;
        esac
    done

    if [[ -z "${cmd}" ]]; then
        if [[ "${cur}" == -* ]]; then
            _appform_global_options
        else
            _appform_commands
        fi
        return
    fi

    case "${cmd}" in
        config)
            if [[ -z "${cmd2}" ]]; then
                _appform_config_subcommands
            fi
            ;;
        extension)
            if [[ -z "${cmd2}" ]]; then
                _appform_extension_subcommands
            fi
            ;;
        endpoint)
            if [[ -z "${cmd2}" ]]; then
                _appform_endpoint_subcommands
            fi
            ;;
        auth)
            if [[ -z "${cmd2}" ]]; then
                _appform_auth_subcommands
            fi
            ;;
        jobs)
            if [[ -z "${cmd2}" ]]; then
                _appform_jobs_subcommands
            elif [[ "${cmd2}" == "list" || "${cmd2}" == "status" ]]; then
                if [[ "${prev}" == "--status" ]]; then
                    _appform_job_statuses
                fi
            fi
            ;;
        sessions)
            if [[ -z "${cmd2}" ]]; then
                _appform_sessions_subcommands
            fi
            ;;
        files)
            if [[ -z "${cmd2}" ]]; then
                _appform_files_subcommands
            elif [[ "${cmd2}" == "ls" || "${cmd2}" == "rm" || "${cmd2}" == "mkdir" || "${cmd2}" == "get" ]]; then
                # Complete remote paths
                if [[ "${cur}" == /* ]]; then
                    COMPREPLY=( $(compgen -f -o plusdirs -P "/" -- "${cur}") )
                fi
            elif [[ "${cmd2}" == "put" ]]; then
                # Complete local paths
                if [[ "${cur}" != /* ]]; then
                    COMPREPLY=( $(compgen -f -- "${cur}") )
                fi
            fi
            ;;
        apps)
            if [[ -z "${cmd2}" ]]; then
                _appform_apps_subcommands
            fi
            ;;
        departments)
            if [[ -z "${cmd2}" ]]; then
                _appform_departments_subcommands
            fi
            ;;
        users)
            if [[ -z "${cmd2}" ]]; then
                _appform_users_subcommands
            fi
            ;;
    esac
}

complete -o nospace -F _appform appform
