# CblDiag_Ansible
## This folder houses all python scripts used in this system

# Files:


* **InvMake_v01** : Script that uses Central based APIs to create a ansible invintory YAML when fed by a flat file of search querys for central groups

Syntax:
```
usage: InvMake_v01.py [-h] -g GROUPFILE [-f FILE] [-v]

optional arguments:
  -h, --help            show this help message and exit
  -g GROUPFILE, --groupfile GROUPFILE (file with groups)
  -f FILE, --file FILE  filename to output CSV data *script will attach json extention
  -v                    Verbose Output

Example:
python InvMake_v01.py -g <Group File> -f <output file>

  ```

* **config.ini**: Configuration file for InvMake_v01. Script requires proper Central API gateway and active OAuth token from Central.

* **StoreList.txt**: Sample flat file used to feed InvMake_v01 script. 

* **CM_Report_v01**: Script to pull data, created by playbook, from the ./Results folder and parse it into a CSV report stored in ./Reports directory 

Syntax:
```
usage: CM_Report_V01.py [-h] -i INVINTORY [-f FILE] [-v]

optional arguments:
  -h, --help            show this help message and exit
  -i INVINTORY, --invintory INVINTORY
                        Input file
  -f FILE, --file FILE  report filename if differant then inv file (csv will be appended)
  -v                    Verbose Output
  ```