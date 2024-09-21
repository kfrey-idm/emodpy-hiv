<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->
**Table of Contents**

- [emodpy-hiv tests](#emodpy-hiv-tests)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->


# emodpy-hiv tests


How to run these tests after you have emodpy-hiv installed in a virtual environment. 

1. Active your virtual environment

2. install dataclasses and keyrings (Linux only) if you haven't installed it
```bash
pip install dataclasses
pip install keyrings.alt (Linux only)
```

3. run unit tests and import tests
```bash
python -m unittest discover .
```

4. run bamboo download test and sim tests

&ensp;&ensp;&ensp;&ensp;4.1. go to tests/sim_tests folder

&ensp;&ensp;&ensp;&ensp;4.2. login to bamboo and cache your credential(need VPN, can skiped if you choose to enter your credential in step 4.3 in console)
```bash
python bamboo_login_with_arguments.py -u youremail@idmod.org -p password
```

&ensp;&ensp;&ensp;&ensp;4.3. download eradication, schema and report plugin files from bamboo(need VPN) and run simulation tests
```bash
python -m unittest discover .
```

&ensp;&ensp;&ensp;&ensp;It may prompt to ask you to enter username and password for bamboo if this is the first time you run this test and didn not run step 4.2

&ensp;&ensp;&ensp;&ensp;It may prompt to ask you to enter username and password for comps2 if your token is expired.
