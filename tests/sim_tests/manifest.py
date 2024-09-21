from pathlib import Path

current_directory = Path(__file__).resolve().parent

config_folder = current_directory / "inputs" / "config"

bin_folder = current_directory / "inputs" / "bin"

eradication_path_win = bin_folder / "Eradication-bamboo.exe"
eradication_path_linux = bin_folder / "Eradication-bamboo"
eradication_path = eradication_path_linux

schema_folder = current_directory / "inputs" / "schema"
schema_path_win = schema_folder / "schema-bamboo.json"
schema_path_linux = schema_folder / "schema-bamboo_l.json"
schema_file = schema_path_linux

plugins_folder_linux = current_directory / "inputs" / "plugins"
plugins_folder_win = current_directory / "inputs" / "plugins_win"
plugins_folder = plugins_folder_linux


demographics_folder = current_directory / "inputs" / "demographics"

campaign_folder = current_directory / "inputs" / "campaigns"

migration_folder = current_directory / "inputs" / 'migration'

ep4_path = current_directory / "inputs" / 'ep4'

requirements = current_directory / 'requirements.txt'

emod_hiv_path = current_directory / "inputs" / "emod-hiv"
emod_hiv_eradication = emod_hiv_path / 'Eradication'
emod_hiv_schema = emod_hiv_path / 'schema.json'