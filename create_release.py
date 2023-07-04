# copy the distribution files to the export directory
import os
import shutil

export_dir = "../export"
os.makedirs(export_dir, exist_ok=True)

package_name = "dynamic_affairs"
package_dir = os.path.join(export_dir, package_name)
# remove the old package
if os.path.exists(package_dir):
    print("Removing old package")
    shutil.rmtree(package_dir)

# directories and files to include
include = ["README.md", "descriptor.mod", "thumbnail.png", "common", "events", "gfx", "gui", "localization"]
# extract the version from the descriptor
with open("descriptor.mod", 'r', encoding='utf-8') as f:
    for line in f:
        if line.startswith("version"):
            version = line.split("=")[1].strip().strip('"')
            break
    else:
        raise Exception("Couldn't find version in descriptor.mod")

print(f"generating release for version {version} for package {package_name}")
os.makedirs(package_dir, exist_ok=True)
for item in include:
    try:
        shutil.copytree(item, os.path.join(package_dir, item))
    except NotADirectoryError:
        shutil.copy(item, os.path.join(package_dir, item))

mod_file = f"{package_name}.mod"
# need to copy this to the export directory and one above the working directory
shutil.copy(mod_file, export_dir)
shutil.copy(mod_file, "../")
