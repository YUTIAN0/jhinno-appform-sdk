"""Users command handler."""

from appform_sdk.cli.common import create_client, output_result


def handle_users_command(args):
    client = create_client(args)
    try:
        if args.users_command == "list":
            result = client.organization.get_users(
                page=args.page,
                page_size=args.page_size,
                dep=getattr(args, "dep", None),
                username=getattr(args, "filter_username", None),
            )
            output_result(result, args.output, "users.list")
        elif args.users_command == "create":
            result = client.organization.create_user(
                username=args.new_username,
                chusername=args.display_name,
                password=args.new_password,
                dep=getattr(args, "dep", None),
                phone=getattr(args, "phone", None),
                mail=getattr(args, "mail", None),
                card=getattr(args, "card", None),
            )
            output_result(result, args.output, "users.create")
        elif args.users_command == "update":
            result = client.organization.update_user(
                username=args.target_username,
                chusername=getattr(args, "display_name", None),
                dep=getattr(args, "dep", None),
                phone=getattr(args, "phone", None),
                mail=getattr(args, "mail", None),
                card=getattr(args, "card", None),
            )
            output_result(result, args.output, "users.update")
        elif args.users_command == "delete":
            result = client.organization.delete_user(username=args.target_username)
            output_result(result, args.output, "users.delete")
        elif args.users_command == "reset-password":
            result = client.organization.reset_password(
                username=args.target_username,
                new_password=args.new_password,
            )
            output_result(result, args.output, "users.reset-password")
    finally:
        client.close()
