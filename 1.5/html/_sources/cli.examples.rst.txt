CLI Examples
============

.. note::

   Please consult the detailed usage in the help of each command
   (use ``-h`` or ``--help`` argument to display the manual).

Running simple sessions
-----------------------

.. code:: shell

  backend.ai run --rm -c 'print("hello world")' python

.. code:: shell

  backend.ai run --rm --exec 'python myscript.py arg1 arg2' \
             python ./myscript.py


Running sessions with accelerators
----------------------------------

.. code:: shell

  backend.ai run --rm -r gpu=0.5 \
             python-tensorflow ./mygpucode.py


Running sessions with vfolders
------------------------------

.. code:: shell

  backend.ai vfolder create mydata1
  backend.ai vfolder upload mydata1 ./bigdata.csv
  backend.ai run --rm -m mydata1 python ...
  backend.ai vfolder download mydata1 ./bigresult.txt


Running parallel experiment sessions
------------------------------------

(TODO)
