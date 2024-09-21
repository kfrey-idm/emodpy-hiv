from pathlib import Path

current_directory = Path(__file__).resolve().parent

emod_hiv_path = current_directory / "inputs" / "emod-hiv"
emod_hiv_eradication = emod_hiv_path / 'Eradication'
emod_hiv_schema = emod_hiv_path / 'schema.json'

sif_path = current_directory / 'stage_sif.id'
