# dozup – Directory of Zips um Processor

This is a simple system for treating a trio of directories as a simple queuing system. The idea is that you 
have other scripts dropping files in the `todo` directory, and this package is used to process them one at 
a time and move the to `done` when they are finished with.

As an additional wrinkle, you can stick a ZIP archive containing files in te `todo` directory, and they 
will be extracted and processed one-by-one.

NOTE. This is a work in progress and is not actually complete or useful yet.
