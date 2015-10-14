difftr finds differences between two different Pentaho Kettle KTR files
much like the usual diff unix utility does for plain text files. difftr
outputs an interactive HTML file showing the step/hop diff of the two
KTRs graphically, and clicking on each step shows normal line diff of
simplified XML fragment of that step. See below for usage:

    $ difftr file1.ktr file2.ktr > file1-file2-diff.html
