"""Extension command handler."""

from appform_sdk.cli.common import create_client, output_result


def handle_extension_command(args):
    if args.extension_command == "list":
        client = create_client(args)
        extensions = client.extension_manager.list_extensions()
        output_result({"extensions": extensions}, args.output)
        client.close()
    elif args.extension_command == "load":
        client = create_client(args)
        client.load_extension_file(args.file)
        print(f"Extension loaded from {args.file}")
        client.close()
