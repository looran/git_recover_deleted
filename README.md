```
usage: git_recover_deleted.py [-h] [-p] [-v] output_dir [filter]

positional arguments:
  output_dir     Output directory
  filter         Filter changes to files name (eg. *.png)

optional arguments:
  -h, --help     show this help message and exit
  -p, --pretend  do not actually copy files
  -v, --verbose  print verbose

go through git history and copy each deleted files to <output_dir>/<filenum>_<commitnum>_<path>
```
