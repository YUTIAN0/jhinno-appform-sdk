"""Endpoint command handler."""

import json
import sys

from appform_sdk.cli.common import create_client, output_result


def handle_endpoint_command(args):
    client = create_client(args)
    if args.endpoint_command == "list":
        version = getattr(args, "version", None)
        if version:
            endpoints = client.registry.get_for_version(version)
        else:
            endpoints = client.registry.get_all()
        output_result(
            {
                "endpoints": {
                    k: {"path": v.path, "method": v.method}
                    for k, v in endpoints.items()
                }
            },
            args.output,
            "endpoint.list",
        )
    elif args.endpoint_command == "call":
        try:
            params = json.loads(args.params) if args.params else None
            data = json.loads(args.data) if args.data else None
            path_params = json.loads(args.path_params) if args.path_params else None
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
            client.close()
            sys.exit(1)
        result = client.call_endpoint(
            args.name, path_params=path_params, params=params, json_data=data
        )
        output_result(result, args.output, "endpoint.call")
    client.close()
