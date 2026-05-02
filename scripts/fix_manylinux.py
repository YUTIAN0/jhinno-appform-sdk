import glob
import os
import re
import subprocess
import sys

bundle = "bundle"

bad = [f for f in glob.glob(os.path.join(bundle, "*-*.whl"))
       if "manylinux_2_" in f and "manylinux2014" not in f]
if not bad:
    sys.exit(0)

bad_by_pkg = {}
for f in bad:
    basename = os.path.basename(f)
    m = re.match(r"([a-zA-Z0-9][\w.-]*)-", basename.replace("_", "-"))
    if m:
        pkg = m.group(1).lower()
        bad_by_pkg.setdefault(pkg, []).append(f)

print(f"=== Fixing {len(bad)} manylinux wheels for older glibc ===")
for pkg, files in bad_by_pkg.items():
    r = subprocess.run(
        [sys.executable, "-m", "pip", "download", "--no-deps",
         "--only-binary", ":all:", "--no-build-isolation",
         "--platform", "manylinux2014_x86_64",
         "--dest", bundle, pkg],
        capture_output=True, text=True
    )
    if r.returncode == 0:
        print(f"  + {pkg}: downloaded manylinux2014 wheel")
    else:
        r2 = subprocess.run(
            [sys.executable, "-m", "pip", "download", "--no-deps",
             "--no-binary", ":all:", "--dest", bundle, pkg],
            capture_output=True, text=True
        )
        if r2.returncode == 0:
            print(f"  + {pkg}: downloaded source tarball (fallback)")
        else:
            print(f"  ! {pkg}: could not get compatible dist", file=sys.stderr)
    for f in files:
        os.remove(f)
        print(f"  - removed: {os.path.basename(f)}")
