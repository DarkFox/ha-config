import os
from collections import defaultdict


async def find_duplicate_filenames(folder_path):
    filename_dict = defaultdict(list)

    for dirpath, dirnames, filenames in os.walk(folder_path):
        for filename in filenames:
            full_path = os.path.join(dirpath, filename)
            filename_dict[filename].append(full_path)

    # Filter out filenames that do not have duplicates
    duplicates = {
        filename: paths for filename, paths in filename_dict.items() if len(paths) > 1
    }

    return duplicates


@service
async def find_duplicate_package_names():
    """yaml
    name: Find Duplicate Package Names
    description: Find duplicate filenames in the config folder and fire an event with the results.
    """
    folder_path = "/config/packages"
    duplicates = find_duplicate_filenames(folder_path)

    event.fire("duplicate_package_names", duplicates=duplicates)