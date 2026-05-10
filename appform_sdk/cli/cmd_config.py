"""Config command handler."""

from appform_sdk.cli.common import output_result
from appform_sdk.config import Config


def handle_config_command(args):
    if args.config_command == "set":
        config_file = getattr(args, "config_file", None)
        cs = getattr(args, "chunk_size", None)
        if cs and not isinstance(cs, int):
            from appform_sdk.files import parse_size

            cs = parse_size(cs)
        Config.save_config_file(
            base_url=args.base_url,
            access_key=args.access_key,
            access_key_secret=args.access_key_secret,
            username=args.username,
            password=getattr(args, "password", None),
            token=args.token,
            timeout=args.timeout,
            verify_ssl=args.verify_ssl,
            api_version=args.api_version,
            extensions_dir=args.extensions_dir,
            job_profile_config=getattr(args, "job_profile_config", None),
            output_format=getattr(args, "output_format", None),
            output_template=getattr(args, "output_template", None),
            default_remote_path=getattr(args, "default_remote_path", None),
            chunk_size=cs,
            default_method=getattr(args, "default_method", None),
            config_file=config_file,
            sftp_host=getattr(args, "sftp_host", None),
            sftp_port=getattr(args, "sftp_port", None),
            sftp_username=getattr(args, "sftp_username", None),
            sftp_password=getattr(args, "sftp_password", None),
            sftp_key_file=getattr(args, "sftp_key_file", None),
            sftp_key_password=getattr(args, "sftp_key_password", None),
            auto_add_host_key=getattr(args, "auto_add_host_key", None),
            http_proxy=getattr(args, "http_proxy", None),
            sftp_proxy=getattr(args, "sftp_proxy", None),
            environment=getattr(args, "environment", None),
        )
        config_path = config_file or Config.get_default_config_path()
        print(f"Configuration saved to {config_path}")
    elif args.config_command == "show":
        config = Config(
            config_file=getattr(args, "config_file", None),
            env=getattr(args, "env", None),
        )
        output_result({"data": config.to_dict()}, args.output, "config.show")
