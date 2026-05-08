"""Apps command handler."""

from appform_sdk.cli.common import create_client, output_result


def handle_apps_command(args):
    client = create_client(args)
    try:
        if args.apps_command == "list":
            result = client.apps.list_all()
            output_result(result, args.output, "apps.list")
        elif args.apps_command == "list-v2":
            result = client.apps.list_v2()
            output_result(result, args.output, "apps.list")
    finally:
        client.close()
