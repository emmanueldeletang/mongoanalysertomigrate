# mongoanalysertomigrate
tools who can help to check compatibility of mongo log and  and source code 

CosmosdbDB mongo  API  Compatibility Tool
This compatibility tool examines log files from MongoDB or source code from MongoDB applications to determine if there are any queries which use operators that are not supported in Cosmosdb Mongo API . This tool produces a simple report of unsupported operators and file names with line numbers for further investigation. this report is save in the local directory based on the output file name you give with the option --O ( becareffull uppercase

Installation
Clone the repository.

Using the tool
This tool supports examining compatibility with either the 4.0 or 4.2 versions of Cosmosdb mongoAPI . The format of the command is:

 python .\analysemongoforcosmosdb.py  --f Filetoscan --O outputfile

or
%%code
python .\analysemongoforcosmosdb.py  --d full-path-to-directory-to-scan --O outputfile

By default the tool will test for Cosmosdb Mongo API  4.2 , include --v 4.0 to test for that specific version.

"full-path-to-file-to-scan" is a single MongoDB log file or source code file to be scanned for compatibility.
"full-path-to-directory-to-scan" is a directory containing MongoDB log files or source code files, all included files will be scanned and subdirectories will be scanned resursively.
NOTE - all files scanned by this utility are opened read-only and scanned in memory. With the exception of operators used there is no logging of the file contents.

Enabling query logging
To enable logging of queries to the MongoDB logs you enable the query profiler and set the slowms to -1, which will cause all queries to be logged. To do so, run the following query from the mongo shell.

db.setProfilingLevel(0, -1)
It is recommended to use a dev/test MongoDB installation to capture the queries, as the logging of all queries can impact production workloads. 

THIS TOOLS CAN ANALYSE mONG ATLAS LOG TOO
