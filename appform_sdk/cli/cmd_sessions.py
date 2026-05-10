"""Sessions command handler."""

from appform_sdk.cli.common import create_client, output_result
from appform_sdk.sessions import try_launch_jhapp_client


def _try_auto_launch(result: dict):
    """Extract jhappUrl from start result and try to launch JHApp client."""
    data = result.get("data", [])
    if not data:
        return

    item = data[0] if isinstance(data, list) else data
    jhapp_url = item.get("jhappUrl", "")
    desktop_id = item.get("desktopId") or item.get("session_id") or item.get("id", "")

    if jhapp_url:
        launched = try_launch_jhapp_client(jhapp_url, desktop_id)
        if launched:
            print("JHApp client launched successfully!")
        else:
            print("Local JHApp client not available, skipping auto-launch.")


def handle_sessions_command(args):
    client = create_client(args)
    try:
        if args.sessions_command == "start":
            result = client.sessions.start(
                app_id=args.app_id,
                start_new=getattr(args, "start_new", None),
                cwd=getattr(args, "cwd", None),
                work_file=getattr(args, "work_file", None),
                param=getattr(args, "param", None),
            )
            output_result(result, args.output, "sessions.start")
            _try_auto_launch(result)
        elif args.sessions_command == "list":
            session_ids = getattr(args, "session_ids", None)
            session_name = getattr(args, "session_name", None)
            if session_ids:
                session_ids = session_ids.split(",")
            result = client.sessions.list(
                session_ids=session_ids, session_name=session_name
            )
            output_result(result, args.output, "sessions.list")
        elif args.sessions_command == "list-all":
            result = client.sessions.list_all(
                page=getattr(args, "page", 1), page_size=getattr(args, "page_size", 20)
            )
            output_result(result, args.output, "sessions.list-all")
        elif args.sessions_command == "connect":
            result = client.sessions.connect(args.session_id)
            output_result(result, args.output, "sessions.connect")
        elif args.sessions_command == "connect-launch":
            result = client.sessions.connect_and_launch(args.session_id)
            output_result(result, args.output, "sessions.connect")
        elif args.sessions_command == "disconnect":
            result = client.sessions.disconnect(args.session_id)
            output_result(result, args.output, "sessions.disconnect")
        elif args.sessions_command == "close":
            result = client.sessions.close(args.session_id)
            output_result(result, args.output, "sessions.close")
        elif args.sessions_command == "share":
            usernames = args.usernames.split(",")
            result = client.sessions.share(
                session_id=args.session_id, usernames=usernames
            )
            output_result(result, args.output, "sessions.share")
    finally:
        client.close()
