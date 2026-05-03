"""Auth command handler."""

from appform_sdk.cli.common import create_client, output_result


def handle_auth_command(args):
    client = create_client(args)
    if args.auth_command == "login":
        result = client.auth.login(username=args.username, password=args.password)
        output_result(result, args.output)
    elif args.auth_command == "ping":
        result = client.auth.ping()
        output_result(result, args.output)
    elif args.auth_command == "logout":
        result = client.auth.logout()
        output_result(result, args.output)
    client.close()
