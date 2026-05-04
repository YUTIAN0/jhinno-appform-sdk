"""Departments command handler."""

from appform_sdk.cli.common import create_client, output_result


def handle_departments_command(args):
    client = create_client(args)
    try:
        if args.departments_command == "list":
            result = client.organization.get_departments()
            output_result(result, args.output, "departments.list")
        elif args.departments_command == "create":
            result = client.organization.create_department(
                dep_name=args.name,
                dep_chname=args.display_name,
                parent_dep=args.parent,
                description=args.description,
            )
            output_result(result, args.output, "departments.create")
        elif args.departments_command == "update":
            result = client.organization.update_department(
                dep_name=args.name,
                dep_chname=args.display_name,
                parent_dep=args.parent,
                description=args.description,
            )
            output_result(result, args.output, "departments.update")
        elif args.departments_command == "delete":
            result = client.organization.delete_department(dep_name=args.name)
            output_result(result, args.output, "departments.delete")
    finally:
        client.close()
