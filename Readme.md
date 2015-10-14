Intro
=====

**difftr** finds differences between two different Pentaho Kettle KTR files
much like the usual diff unix utility does for plain text files. difftr
outputs an interactive HTML file showing the step/hop diff of the two
KTRs graphically, and clicking on each step shows normal line diff of
simplified XML fragment of that step. See below for usage:

    $ difftr file1.ktr file2.ktr > file1-file2-diff.html

difftr requires python 3 and graphviz.

Output
======

White steps in the output indicate no change to that step. Yellow steps
indicate change (e.g. modified SQL for a Table Input step). To view the
change, click on the step. Red steps indicate they've been deleted and
green steps, added. Similarly, red arrows indicate removed hops and
green ones indicate added.
