import os

current_directory = os.path.dirname(os.path.realpath(__file__))

package_folder = os.path.join(current_directory, "download")
schema_path = os.path.join(package_folder, "schema.json")
eradication_path = os.path.join(package_folder, "Eradication")


def delete_existing_file(file):
    if os.path.isfile(file):
        print(f'\tremove existing {file}.')
        os.remove(file)
