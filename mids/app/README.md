# API README.md
GitHub Pages provide minimal support for dynamic content such as content returned by a local API request. 
Accordingly, JSON response bodies that would normally be returned by an API, are stored as static JSON files in 
the /api directory.

## Procedure
* python freeze.py build - Generates the static JSON files in the /api directory.
* Make sure the proper extension *.json is added to the file name.
* Copy the content of the /build directory in StaDocGen to the /docs directory in the MIDS repository, then commit MIDS.
* The JavaScript code makes a request to the URL https://tdwg.github.io/mids/api/filters.json and https://tdwg.github.io/mids/api/data.json. If the files are committed properly to the build directory, the fetch requests should work correctly and avoid triggering the CORS errors.

* For the interactive mappings table to work, both JSON endpoints must be saved to files and included in the build directory.
* When testing the json files can be stored using http://127.0.0.1:8001/api/filters.json and 

Last Updated: 2025-10-15