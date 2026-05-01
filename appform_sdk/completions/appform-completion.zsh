#compdef appform
# zsh completion for appform SDK
# Install: source appform-completion.zsh or copy to ~/.zsh/completion/
# Or: add to ~/.zshrc: fpath=(~/.zsh/completion $fpath); compinit

_appform() {
    local -a _main_commands
    _main_commands=(
        'config:Manage configuration'
        'extension:Manage extensions'
        'endpoint:Manage endpoints'
        'auth:Authentication operations'
        'jobs:Job operations'
        'sessions:Session operations'
        'files:File operations (Linux-like)'
        'apps:Application operations'
        'departments:Department operations'
        'users:User operations'
    )

    local -a _global_options
    _global_options=(
        '--base-url[API base URL]'
        '--access-key[Access key]'
        '--access-key-secret[Access key secret]'
        '--username[Username]'
        '--password[Password]'
        '--token[Authentication token]'
        '--api-version[API version (default: 6.5)]'
        '--extensions-dir[Extensions directory]'
        '--config[Path to configuration file]'
        '--output[Output format: json/raw/table/text]: :(json raw table text)'
        '-o[Output format: json/raw/table/text]: :json raw table text'
        '--output-template[Output template file (.yaml/.yml/.json)]'
        '--profile-config[Job profile config file]'
        '--version[Show version]'
    )

    local -a _config_subcmds
    _config_subcmds=(
        'set:Set configuration values'
        'show:Show current configuration'
    )

    local -a _extension_subcmds
    _extension_subcmds=(
        'list:List loaded extensions'
        'load:Load an extension from file'
    )

    local -a _endpoint_subcmds
    _endpoint_subcmds=(
        'list:List registered endpoints'
        'call:Call an endpoint by name'
    )

    local -a _auth_subcmds
    _auth_subcmds=(
        'login:Login with username and password'
        'ping:Test authentication'
        'logout:Logout'
    )

    local -a _jobs_subcmds
    _jobs_subcmds=(
        'apps:List applications from config'
        'params:Show application parameters'
        'submit:Submit a job'
        'submit-raw:Submit a job with raw JSON'
        'list:List jobs'
        'status:List jobs by status'
        'get:Get job details'
        'stop:Stop a job'
        'suspend:Suspend a job'
        'resume:Resume a job'
        'output:Get job output'
        'files:Get job files'
        'history:Get job history'
        'history-page:List history with pagination'
        'delete:Delete a job'
        'form:Get job submission form (6.6+)'
        'tooltip:Get job monitoring info (6.6+)'
    )

    local -a _sessions_subcmds
    _sessions_subcmds=(
        'start:Start a new session'
        'list:Query sessions (current user)'
        'list-all:List all sessions'
        'connect:Get session connection info'
        'connect-launch:Connect and auto-launch JHApp client'
        'disconnect:Disconnect a session'
        'close:Close a session'
        'share:Share a session'
    )

    local -a _files_subcmds
    _files_subcmds=(
        'ls:List remote directory'
        'cp:Copy remote file'
        'mv:Move/rename remote file'
        'rm:Delete remote file'
        'mkdir:Create remote directory'
        'put:Upload local file to remote'
        'get:Download remote file to local'
        'compress:Compress remote directory'
        'uncompress:Uncompress remote archive'
        'conf:File confidentiality operations'
    )

    local -a _apps_subcmds
    _apps_subcmds=(
        'list:List all applications (6.0+)'
        'list-v2:List available apps v2 (6.6+)'
    )

    local -a _departments_subcmds
    _departments_subcmds=(
        'list:List departments (tree)'
        'create:Create department'
        'update:Update department'
        'delete:Delete department'
    )

    local -a _users_subcmds
    _users_subcmds=(
        'list:List users'
        'create:Create user'
        'update:Update user'
        'delete:Delete user'
        'reset-password:Reset user password'
    )

    local -a _job_statuses
    _job_statuses=(
        'RUN:Running'
        'PEND:Pending'
        'DONE:Done'
        'EXIT:Exited'
    )

    local -a _output_formats
    _output_formats=(
        'json:JSON format'
        'raw:Raw API response'
        'table:Table format (default)'
        'text:Plain text'
    )

    local states=()
    states+=(
        'line'
        '_values "appform commands" _main_commands'
    )

    local context
    _arguments -C \
        '(-)*: :->global_opts' \
        '(-)--base-url[API base URL]: :->' \
        '(-)--access-key[Access key]: :->' \
        '(-)--access-key-secret[Access key secret]: :->' \
        '(-)--username[Username]: :->' \
        '(-)--password[Password]: :->' \
        '(-)--token[Authentication token]: :->' \
        '(-)--api-version[API version]: :->' \
        '(-)--extensions-dir[Extensions directory]: :->' \
        '(-)--config[Configuration file]:(*)' \
        '(-)--output[Output format]:_output_fmts' \
        '(-)-o[Output format short]:_output_fmts' \
        '(-)--output-template[Output template file]:(*.yaml *.yml *.json)' \
        '(-)--profile-config[Job profile config]:(*)' \
        '(- 1):command:->cmds' \
        '*' && return 0

    local -a _output_fmts
    _output_fmts=(
        'json:JSON format'
        'raw:Raw API response'
        'table:Table format'
        'text:Plain text'
    )

    case "$state" in
    cmds)
        local cmd="${words[2]}"
        case "${cmd}" in
            config)
                _describe 'command' _config_subcmds && return
                ;;
            extension)
                _describe 'command' _extension_subcmds && return
                ;;
            endpoint)
                _describe 'command' _endpoint_subcmds && return
                ;;
            auth)
                _describe 'command' _auth_subcmds && return
                ;;
            jobs)
                _describe 'command' _jobs_subcmds && return
                ;;
            sessions)
                _describe 'command' _sessions_subcmds && return
                ;;
            files)
                _describe 'command' _files_subcmds && return
                ;;
            apps)
                _describe 'command' _apps_subcmds && return
                ;;
            departments)
                _describe 'command' _departments_subcmds && return
                ;;
            users)
                _describe 'command' _users_subcmds && return
                ;;
            *)
                _describe 'command' _main_commands
                ;;
        esac
        ;;
    esac
}

_appform
