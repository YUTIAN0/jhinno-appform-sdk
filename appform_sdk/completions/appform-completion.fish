# fish completion for appform SDK
# Install: copy to ~/.config/fish/completions/appform.fish
# Or: appform --generate-completion fish > ~/.config/fish/completions/appform.fish

# Global options
complete -c appform -n "__fish_appform_needs_command" -l base-url -r -d 'API base URL'
complete -c appform -n "__fish_appform_needs_command" -l access-key -r -d 'Access key'
complete -c appform -n "__fish_appform_needs_command" -l access-key-secret -r -d 'Access key secret'
complete -c appform -n "__fish_appform_needs_command" -l username -r -d 'Username'
complete -c appform -n "__fish_appform_needs_command" -l password -r -d 'Password'
complete -c appform -n "__fish_appform_needs_command" -l token -r -d 'Authentication token'
complete -c appform -n "__fish_appform_needs_command" -l api-version -r -d 'API version'
complete -c appform -n "__fish_appform_needs_command" -l extensions-dir -r -d 'Extensions directory'
complete -c appform -n "__fish_appform_needs_command" -l config -r -d 'Configuration file'
complete -c appform -n "__fish_appform_needs_command" -s o -l output -x -a '{json\ "JSON format",raw\ "Raw API response",table\ "Table format",text\ "Plain text"}' -d 'Output format'
complete -c appform -n "__fish_appform_needs_command" -l output-template -r -d 'Output template file'
complete -c appform -n "__fish_appform_needs_command" -l profile-config -r -d 'Job profile config'
complete -c appform -n "__fish_appform_needs_command" -l env -r -d 'Target environment'
complete -c appform -n "__fish_appform_needs_command" -l http-proxy -r -d 'HTTP/HTTPS proxy URL'
complete -c appform -n "__fish_appform_needs_command" -l sftp-proxy -r -d 'SFTP/SSH proxy URL'
complete -c appform -n "__fish_appform_needs_command" -l version -d 'Show version'

# Main commands
complete -c appform -n "__fish_appform_needs_command" -f -a config -d 'Manage configuration'
complete -c appform -n "__fish_appform_needs_command" -f -a extension -d 'Manage extensions'
complete -c appform -n "__fish_appform_needs_command" -f -a endpoint -d 'Manage endpoints'
complete -c appform -n "__fish_appform_needs_command" -f -a auth -d 'Authentication'
complete -c appform -n "__fish_appform_needs_command" -f -a jobs -d 'Job operations'
complete -c appform -n "__fish_appform_needs_command" -f -a sessions -d 'Session operations'
complete -c appform -n "__fish_appform_needs_command" -f -a files -d 'File operations'
complete -c appform -n "__fish_appform_needs_command" -f -a apps -d 'Application operations'
complete -c appform -n "__fish_appform_needs_command" -f -a departments -d 'Department operations'
complete -c appform -n "__fish_appform_needs_command" -f -a users -d 'User operations'

# --- config ---
complete -c appform -n "__fish_appform_using_command config" -f -a set -d 'Set configuration values'
complete -c appform -n "__fish_appform_using_command config" -f -a show -d 'Show current configuration'
complete -c appform -n "__fish_appform_using_command config; and __fish_seen_subcommand_from set" -l base-url -r
complete -c appform -n "__fish_appform_using_command config; and __fish_seen_subcommand_from set" -l access-key -r
complete -c appform -n "__fish_appform_using_command config; and __fish_seen_subcommand_from set" -l access-key-secret -r
complete -c appform -n "__fish_appform_using_command config; and __fish_seen_subcommand_from set" -l username -r
complete -c appform -n "__fish_appform_using_command config; and __fish_seen_subcommand_from set" -l password -r
complete -c appform -n "__fish_appform_using_command config; and __fish_seen_subcommand_from set" -l token -r
complete -c appform -n "__fish_appform_using_command config; and __fish_seen_subcommand_from set" -l timeout -r
complete -c appform -n "__fish_appform_using_command config; and __fish_seen_subcommand_from set" -l verify-ssl -r
complete -c appform -n "__fish_appform_using_command config; and __fish_seen_subcommand_from set" -l api-version -r
complete -c appform -n "__fish_appform_using_command config; and __fish_seen_subcommand_from set" -l extensions-dir -r
complete -c appform -n "__fish_appform_using_command config; and __fish_seen_subcommand_from set" -l job-profile-config -r
complete -c appform -n "__fish_appform_using_command config; and __fish_seen_subcommand_from set" -l output-format -x -a '{json\ "JSON format",raw\ "Raw API response",table\ "Table format",text\ "Plain text"}'
complete -c appform -n "__fish_appform_using_command config; and __fish_seen_subcommand_from set" -l output-template -r
complete -c appform -n "__fish_appform_using_command config; and __fish_seen_subcommand_from set" -l default-remote-path -r
complete -c appform -n "__fish_appform_using_command config; and __fish_seen_subcommand_from set" -l chunk-size -r

# --- extension ---
complete -c appform -n "__fish_appform_using_command extension" -f -a list -d 'List loaded extensions'
complete -c appform -n "__fish_appform_using_command extension" -f -a load -d 'Load an extension'
complete -c appform -n "__fish_appform_using_command extension; and __fish_seen_subcommand_from load" -r -d 'Extension file'

# --- endpoint ---
complete -c appform -n "__fish_appform_using_command endpoint" -f -a list -d 'List registered endpoints'
complete -c appform -n "__fish_appform_using_command endpoint" -f -a call -d 'Call an endpoint'
complete -c appform -n "__fish_appform_using_command endpoint; and __fish_seen_subcommand_from list" -l version -r
complete -c appform -n "__fish_appform_using_command endpoint; and __fish_seen_subcommand_from call" -l params -r
complete -c appform -n "__fish_appform_using_command endpoint; and __fish_seen_subcommand_from call" -l data -r
complete -c appform -n "__fish_appform_using_command endpoint; and __fish_seen_subcommand_from call" -l path-params -r
complete -c appform -n "__fish_appform_using_command endpoint; and __fish_seen_subcommand_from call" -r -d 'Endpoint name (e.g., jobs.list)'

# --- auth ---
complete -c appform -n "__fish_appform_using_command auth" -f -a login -d 'Login with username and password'
complete -c appform -n "__fish_appform_using_command auth" -f -a ping -d 'Test authentication'
complete -c appform -n "__fish_appform_using_command auth" -f -a logout -d 'Logout'
complete -c appform -n "__fish_appform_using_command auth; and __fish_seen_subcommand_from login" -l username -r -r
complete -c appform -n "__fish_appform_using_command auth; and __fish_seen_subcommand_from login" -l password -r -r

# --- jobs ---
complete -c appform -n "__fish_appform_using_command jobs" -f -a apps -d 'List applications'
complete -c appform -n "__fish_appform_using_command jobs" -f -a params -d 'Show application parameters'
complete -c appform -n "__fish_appform_using_command jobs" -f -a submit -d 'Submit a job'
complete -c appform -n "__fish_appform_using_command jobs" -f -a submit-raw -d 'Submit with raw JSON'
complete -c appform -n "__fish_appform_using_command jobs" -f -a list -d 'List jobs'
complete -c appform -n "__fish_appform_using_command jobs" -f -a status -d 'List jobs by status'
complete -c appform -n "__fish_appform_using_command jobs" -f -a get -d 'Get job details'
complete -c appform -n "__fish_appform_using_command jobs" -f -a stop -d 'Stop a job'
complete -c appform -n "__fish_appform_using_command jobs" -f -a suspend -d 'Suspend a job'
complete -c appform -n "__fish_appform_using_command jobs" -f -a resume -d 'Resume a job'
complete -c appform -n "__fish_appform_using_command jobs" -f -a output -d 'Get job output'
complete -c appform -n "__fish_appform_using_command jobs" -f -a files -d 'Get job files'
complete -c appform -n "__fish_appform_using_command jobs" -f -a history -d 'Get job history'
complete -c appform -n "__fish_appform_using_command jobs" -f -a history-page -d 'List history with pagination'
complete -c appform -n "__fish_appform_using_command jobs" -f -a delete -d 'Delete a job'
complete -c appform -n "__fish_appform_using_command jobs" -f -a form -d 'Get job submission form'
complete -c appform -n "__fish_appform_using_command jobs" -f -a tooltip -d 'Get job monitoring info'
# jobs list options
complete -c appform -n "__fish_appform_using_command jobs; and __fish_seen_subcommand_from list" -l page -r
complete -c appform -n "__fish_appform_using_command jobs; and __fish_seen_subcommand_from list" -l page-size -r
complete -c appform -n "__fish_appform_using_command jobs; and __fish_seen_subcommand_from list" -l status -x -a '{RUN\ "Running",PEND\ "Pending",DONE\ "Done",EXIT\ "Exited"}'
complete -c appform -n "__fish_appform_using_command jobs; and __fish_seen_subcommand_from list" -l name -r
complete -c appform -n "__fish_appform_using_command jobs; and __fish_seen_subcommand_from list" -l job-id -r
complete -c appform -n "__fish_appform_using_command jobs; and __fish_seen_subcommand_from status" -x -a '{RUN\ "Running",PEND\ "Pending",DONE\ "Done",EXIT\ "Exited",all\ "All statuses"}'
complete -c appform -n "__fish_appform_using_command jobs; and __fish_seen_subcommand_from status" -l page -r
complete -c appform -n "__fish_appform_using_command jobs; and __fish_seen_subcommand_from status" -l page-size -r
complete -c appform -n "__fish_appform_using_command jobs; and __fish_seen_subcommand_from submit-raw" -l app-id -r
complete -c appform -n "__fish_appform_using_command jobs; and __fish_seen_subcommand_from submit-raw" -l params -r
# submit options
complete -c appform -n "__fish_appform_using_command jobs; and __fish_seen_subcommand_from submit" -s a -l app -r -d 'Application type'
complete -c appform -n "__fish_appform_using_command jobs; and __fish_seen_subcommand_from submit" -s l -l list-apps -d 'List applications'
complete -c appform -n "__fish_appform_using_command jobs; and __fish_seen_subcommand_from submit" -l set -r -d 'Override parameter KEY=VALUE'
complete -c appform -n "__fish_appform_using_command jobs; and __fish_seen_subcommand_from submit" -l params -r -d 'Parameters as JSON'
complete -c appform -n "__fish_appform_using_command jobs; and __fish_seen_subcommand_from submit" -l dry-run -d 'Preview without submitting'

# --- sessions ---
complete -c appform -n "__fish_appform_using_command sessions" -f -a start -d 'Start a new session'
complete -c appform -n "__fish_appform_using_command sessions" -f -a list -d 'Query sessions'
complete -c appform -n "__fish_appform_using_command sessions" -f -a list-all -d 'List all sessions'
complete -c appform -n "__fish_appform_using_command sessions" -f -a connect -d 'Get session connection info'
complete -c appform -n "__fish_appform_using_command sessions" -f -a connect-launch -d 'Connect and auto-launch client'
complete -c appform -n "__fish_appform_using_command sessions" -f -a disconnect -d 'Disconnect a session'
complete -c appform -n "__fish_appform_using_command sessions" -f -a close -d 'Close a session'
complete -c appform -n "__fish_appform_using_command sessions" -f -a share -d 'Share a session'
complete -c appform -n "__fish_appform_using_command sessions; and __fish_seen_subcommand_from start" -l app-id -r
complete -c appform -n "__fish_appform_using_command sessions; and __fish_seen_subcommand_from start" -l start-new
complete -c appform -n "__fish_appform_using_command sessions; and __fish_seen_subcommand_from start" -l cwd -r
complete -c appform -n "__fish_appform_using_command sessions; and __fish_seen_subcommand_from start" -l work-file -r
complete -c appform -n "__fish_appform_using_command sessions; and __fish_seen_subcommand_from start" -l param -r
complete -c appform -n "__fish_appform_using_command sessions; and __fish_seen_subcommand_from list" -l ids -r
complete -c appform -n "__fish_appform_using_command sessions; and __fish_seen_subcommand_from list" -l name -r
complete -c appform -n "__fish_appform_using_command sessions; and __fish_seen_subcommand_from list-all" -l page -r
complete -c appform -n "__fish_appform_using_command sessions; and __fish_seen_subcommand_from list-all" -l page-size -r
complete -c appform -n "__fish_appform_using_command sessions; and __fish_seen_subcommand_from share" -l usernames -r

# --- files ---
complete -c appform -n "__fish_appform_using_command files" -f -a ls -d 'List remote directory'
complete -c appform -n "__fish_appform_using_command files" -f -a cp -d 'Copy remote file'
complete -c appform -n "__fish_appform_using_command files" -f -a mv -d 'Move/rename remote file'
complete -c appform -n "__fish_appform_using_command files" -f -a rm -d 'Delete remote file'
complete -c appform -n "__fish_appform_using_command files" -f -a mkdir -d 'Create remote directory'
complete -c appform -n "__fish_appform_using_command files" -f -a put -d 'Upload local file to remote'
complete -c appform -n "__fish_appform_using_command files" -f -a get -d 'Download remote file to local'
complete -c appform -n "__fish_appform_using_command files" -f -a compress -d 'Compress remote directory'
complete -c appform -n "__fish_appform_using_command files" -f -a uncompress -d 'Uncompress remote archive'
complete -c appform -n "__fish_appform_using_command files" -f -a conf -d 'File confidentiality'
complete -c appform -n "__fish_appform_using_command files; and __fish_seen_subcommand_from ls" -l page -r
complete -c appform -n "__fish_appform_using_command files; and __fish_seen_subcommand_from ls" -l page-size -r
complete -c appform -n "__fish_appform_using_command files; and __fish_seen_subcommand_from ls" -s a -l all -d 'List all with auto-pagination'
complete -c appform -n "__fish_appform_using_command files; and __fish_seen_subcommand_from put" -s f -l force -d 'Overwrite existing'
complete -c appform -n "__fish_appform_using_command files; and __fish_seen_subcommand_from put" -l chunk-size -r
complete -c appform -n "__fish_appform_using_command files; and __fish_seen_subcommand_from get" -l chunk-size -r
complete -c appform -n "__fish_appform_using_command files; and __fish_seen_subcommand_from conf" -l get-levels -d 'Get confidentiality levels'
complete -c appform -n "__fish_appform_using_command files; and __fish_seen_subcommand_from conf" -l set -r -d 'Set file confidentiality: PATH LEVEL'

# --- apps ---
complete -c appform -n "__fish_appform_using_command apps" -f -a list -d 'List all applications'
complete -c appform -n "__fish_appform_using_command apps" -f -a list-v2 -d 'List available apps v2 (6.6+)'

# --- departments ---
complete -c appform -n "__fish_appform_using_command departments" -f -a list -d 'List departments'
complete -c appform -n "__fish_appform_using_command departments" -f -a create -d 'Create department'
complete -c appform -n "__fish_appform_using_command departments" -f -a update -d 'Update department'
complete -c appform -n "__fish_appform_using_command departments" -f -a delete -d 'Delete department'
complete -c appform -n "__fish_appform_using_command departments; and __fish_seen_subcommand_from create" -l name -r
complete -c appform -n "__fish_appform_using_command departments; and __fish_seen_subcommand_from create" -l display-name -r
complete -c appform -n "__fish_appform_using_command departments; and __fish_seen_subcommand_from create" -l parent -r
complete -c appform -n "__fish_appform_using_command departments; and __fish_seen_subcommand_from create" -l description -r
complete -c appform -n "__fish_appform_using_command departments; and __fish_seen_subcommand_from update" -l name -r
complete -c appform -n "__fish_appform_using_command departments; and __fish_seen_subcommand_from update" -l display-name -r
complete -c appform -n "__fish_appform_using_command departments; and __fish_seen_subcommand_from update" -l parent -r
complete -c appform -n "__fish_appform_using_command departments; and __fish_seen_subcommand_from update" -l description -r
complete -c appform -n "__fish_appform_using_command departments; and __fish_seen_subcommand_from delete" -l name -r

# --- users ---
complete -c appform -n "__fish_appform_using_command users" -f -a list -d 'List users'
complete -c appform -n "__fish_appform_using_command users" -f -a create -d 'Create user'
complete -c appform -n "__fish_appform_using_command users" -f -a update -d 'Update user'
complete -c appform -n "__fish_appform_using_command users" -f -a delete -d 'Delete user'
complete -c appform -n "__fish_appform_using_command users" -f -a reset-password -d 'Reset user password'
complete -c appform -n "__fish_appform_using_command users; and __fish_seen_subcommand_from list" -l page -r
complete -c appform -n "__fish_appform_using_command users; and __fish_seen_subcommand_from list" -l page-size -r
complete -c appform -n "__fish_appform_using_command users; and __fish_seen_subcommand_from list" -l dep -r
complete -c appform -n "__fish_appform_using_command users; and __fish_seen_subcommand_from list" -l filter-username -r
complete -c appform -n "__fish_appform_using_command users; and __fish_seen_subcommand_from create" -l user -r
complete -c appform -n "__fish_appform_using_command users; and __fish_seen_subcommand_from create" -l display-name -r
complete -c appform -n "__fish_appform_using_command users; and __fish_seen_subcommand_from create" -l new-password -r
complete -c appform -n "__fish_appform_using_command users; and __fish_seen_subcommand_from create" -l dep -r
complete -c appform -n "__fish_appform_using_command users; and __fish_seen_subcommand_from create" -l phone -r
complete -c appform -n "__fish_appform_using_command users; and __fish_seen_subcommand_from create" -l mail -r
complete -c appform -n "__fish_appform_using_command users; and __fish_seen_subcommand_from create" -l card -r
complete -c appform -n "__fish_appform_using_command users; and __fish_seen_subcommand_from update" -l user -r
complete -c appform -n "__fish_appform_using_command users; and __fish_seen_subcommand_from update" -l display-name -r
complete -c appform -n "__fish_appform_using_command users; and __fish_seen_subcommand_from update" -l dep -r
complete -c appform -n "__fish_appform_using_command users; and __fish_seen_subcommand_from update" -l phone -r
complete -c appform -n "__fish_appform_using_command users; and __fish_seen_subcommand_from update" -l mail -r
complete -c appform -n "__fish_appform_using_command users; and __fish_seen_subcommand_from update" -l card -r
complete -c appform -n "__fish_appform_using_command users; and __fish_seen_subcommand_from delete" -l user -r
complete -c appform -n "__fish_appform_using_command users; and __fish_seen_subcommand_from reset-password" -l user -r
complete -c appform -n "__fish_appform_using_command users; and __fish_seen_subcommand_from reset-password" -l new-password -r

# Helper functions
function __fish_appform_needs_command
    set cmd (commandline -opc)
    for x in $cmd
        switch $x
            case config extension endpoint auth jobs sessions files apps departments users
                return 1
        end
    end
    return 0
end

function __fish_appform_using_command
    set cmd (commandline -opc)
    set -l found 0
    for x in $cmd
        if test $x = $argv[1]
            set found 1
        end
        if test $found = 1
            return 1
        end
    end
    test $found = 1
end
