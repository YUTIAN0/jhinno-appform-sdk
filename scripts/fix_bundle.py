"""Replace manylinux_2_XX wheels with manylinux2014 variants for older glibc compatibility."""

import glob
import os
import subprocess
import sys


def main():
    bundle_dir = sys.argv[1] if len(sys.argv) > 1 else "bundle"

    bad = [
        f
        for f in glob.glob(os.path.join(bundle_dir, "*-*.whl"))
        if "manylinux_2_" in f and "manylinux2014" not in f
    ]
    if not bad:
        print("No incompatible manylinux wheels found.")
        return

    # Group by package name
    bad_by_pkg = {}
    for f in bad:
        basename = os.path.basename(f)
        parts = basename.split("-")
        if len(parts) >= 2:
            pkg = parts[0].lower()
            bad_by_pkg.setdefault(pkg, []).append(f)

    print(f"=== Fixing {len(bad)} manylinux wheels for older glibc ===")
    for pkg, files in bad_by_pkg.items():
        # Try manylinux2014 wheel
        r = subprocess.run(
            [
                sys.executable,
                "-m",
                "pip",
                "download",
                "--no-deps",
                "--only-binary",
                ":all:",
                "--platform",
                "manylinux2014_x86_64",
                "--dest",
                bundle_dir,
                pkg,
            ],
            capture_output=True,
            text=True,
        )
        if r.returncode == 0:
            print(f"  + {pkg}: downloaded manylinux2014 wheel")
        else:
            # Fallback: source tarball
            r2 = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "download",
                    "--no-deps",
                    "--no-binary",
                    ":all:",
                    "--dest",
                    bundle_dir,
                    pkg,
                ],
                capture_output=True,
                text=True,
            )
            if r2.returncode == 0:
                print(f"  + {pkg}: downloaded source tarball (fallback)")
            else:
                print(
                    f"  ! {pkg}: could not get compatible dist",
                    file=sys.stderr,
                )
        # Remove incompatible wheels
        for f in files:
            os.remove(f)
            print(f"  - removed: {os.path.basename(f)}")


if __name__ == "__main__":
    main()
