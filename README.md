Jabberd14 with MySQL Flavor to Openfire
=======================================

This is a small and rather stupid python script to convert a Jabberd14
MySQL database into a XML file to be used with Openfires generic import
/ export plugin. The script is splitted into an input and an output
section, implementing other migration targets should be easy.

Dependencies:
* Python 3.4 (older version may work but they're untested)
* pymsql (https://github.com/PyMySQL/PyMySQL)
* xmltodict (https://github.com/martinblech/xmltodict)

To use the script open it in a text editor and change the variables at
the top of the file to match your setup. After that run the script. The
source database is just read and never written. So the jabberd14 setup
isn't touched at all.

