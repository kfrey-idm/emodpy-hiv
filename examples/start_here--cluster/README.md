# HIV Example Scenario (cluster version)

These instructions have been tested with singularity version 3.9.1, python version 3.8.11 x64, and should be considered minimum requirements.

- Log into your cluster to open a fresh terminal

- Verify your currently available version of apptainer/singularity and python:
```
singularity --version   # apptainer --version
python --version
```

- Navigate to where you would like to set up your example and place a copy of the example directory contents there.

- Create python virtual environment to use
```
python -m venv env-emodpy-hiv-38
```

- Edit file env-emodpy-hiv-38/pip.conf to contain exactly the following. This tells pip where to find IDM software:
```
[global]
index-url = https://packages.idmod.org/api/pypi/pypi-production/simple
```

- Activate virtual environment
```
source env-emodpy-hiv-38/bin/activate
```

- Install software into virtual environment
```
python -m pip install --upgrade pip
python -m pip install emodpy-hiv
python -m pip install idmtools-platform-slurm
python -m pip install eradicationpy
```

- Edit your idmtools.ini file, [CLUSTER] block:
  - change the settings to match your cluster and notification email address

- Edit your manifest.py file:
  - update the location of the sif file you will be using to run EMOD inside of (parameter sif_path)

- Run the example:
```
python example.py
```

- If you get an error similar to "bash: singularity: command not found" (because you use apptainer instead of singularity) try the following and then re-run example.py:
```
mkdir -p ~/bin
which apptainer
ln -s FULL_PATH_TO_APPTAINER_IN_RESULT ~/bin/singularity
export PATH=$PATH:~/bin    # It is suggested to add this line to your ~/.bashrc file as well, so you don't need to do this again in the future
```

- Inspect simulation results. They are located in the ./simulations directory (relative to example.py), nested in SUITE_ID/EXPERIMENT_ID/SIM_ID directories
