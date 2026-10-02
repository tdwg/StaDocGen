# StaDocGen
Web-based Documentation Generator for TDWG Data Standards  
Built using Python Flask, StaDocGen transforms a set of CSV files into data standard documentation in HTML format. 

## Application Specifications

### Naming Conventions for Files
| Extension | Convention                              | Example              |
| --------- | --------------------------------------- | -------------------- |
| html      | Concepts are separated with hyphens     | quick-reference.html |
| py        | Concepts are separated with underscores | quick_reference.py   |
| md        | Concepts are separated with underscores | quick_reference.md   |
| (folder)  | Concepts are separated with underscores | app/quick_reference/ |
| csv       | Concepts are separated with hyphens     | quick-reference.csv  |

```
├───app
│   ├───build            | Static html files generated using Frozen Flask (https://pythonhosted.org/Frozen-Flask/)
│   ├───data             | Standard data 
│   │   ├───output       | Output from the transformation of source data files used for documentation webpages
│   │   └───source       | Original source data files
│   ├───md               | Latest versions of official TDWG documentation markdown content, these files are then customized for each standard
│   ├───static           | Static assets (css, js, icons)
│   │   └───assets       | Standard static assets (do not change)
│   │   └───images       | Stanard-specific custom imagery 
│   │   └───custom       | Customized CSS overrides and javascript files that extend and alter the standardized template files under assets.
│   ├───templates        | Jinja templates
│   │   └───includes     | Page components partitioned into folders based on scope
│   ├───utils            | Data transformation utilities 
│   │   └───analysis     | Various scripts for analysis of source and output data files
│   │   └───schemas      | Tabular data schemas generated from the source CSV files
│   │   └───transformers | Scripts that transform source data files into output used to generate the documentation webpages

_init__.py
freeze.py   Frozen flask script to generate build files
routes.py   Dynamic flask script (deprecated in newer instances of StaDocGen
```

### Organization of StaDocGen
StaDocGen is structured as a collection of top-level folders for every documentation website due to a number of technological constraints. 
We call these ***instances*** of StaDocGen. Documentation websites are created independently, and instances do not share resources*. 
Please take note of the scope of each of the following processes; some are unique to a single instance or group of instances, while 
others are applicable to all standards indicated as global.

* *The shared directory contains a starter set of files to create new instances of StaDocGen. The first step to adding a new standard is to create a copy of the shared folder then rename it using the namespace of the standard. 

### Commands
Creating the Environment
* Stadocgen was created using Windows 11, PyCharm Professional, Python 3.11 and the Package Manager PIP
* For information on how to install Python 3.11 and the package manager, PIP, please refer to the respective documentation pages

The $ signifies the start of a new command in the command line window (also colled the console). For Windows users, 
I highly recommend using ConEmu https://conemu.github.io/ or Git Bash. You can also use the default console window by:
1. Press the Windows Key
2. Type cmd
3. Press enter

### Install Packages - Global
* Open command line window
* Navigate to the root directory of this repository
* Run the following commands
  * $python -m venv .stadocgen-venv
  * **Windows**:
       * $.\.stadocgen-venv\Scripts\activate
  * **Mac/Linux**:
       * $source .stadocgen-venv/bin/activate
  * $pip install -r requirements.txt
* To test pages, go to **Testing**
* To build webpages for publication, go to **Build Documentation Pages**

### Before Running
* Make sure to copy the latest version of the page markdown files from the standard repository. In the case of Latimer Core, these files reside in the LtC Repo here: [https://github.com/tdwg/ltc/tree/main/source/md](https://github.com/tdwg/ltc/tree/main/source/md)
* If you haven't already, open the meta.yml metadata file and enter the appropriate information for your standard.

### Testing
* Open the command line window and navigate to the instance root directory (e.g. (root)/ltc)
* Make sure the virtual environment is activated (conda activate stadcogen-venv or .\.stadocgen-venv\Scripts\activate)
* At the cmd line, enter $flask run
* Open a browser to localhost:5000
* To end testing and stop the development server, press CTRL+C in the command line window

### Build Documentation Pages
* Open a command prompt in the app subdirectory of the instance (e.g. /ltc/app) 
* Enter *python freeze.py build*
* Copy the entire contents of the build directory (/app/build) to the docs folder in the target repository
* Publish changes using the appropriate GitHub workflow

Using Windows, robocopy can be used to replace files in a target directory with a source. The following command will accomplish this task (before using, make sure to update the paths)  
robocopy C:\repos\stadocgen\app\build G:\repos\ltc\docs /mir
Once the new build is pushed to the target repo, continue the standard protocol for updating a repository (create new branch with updated docs > pull request > approve > merge).  

### Important Changes between routes.py and freeze.py
1. In freeze.py, all route names must be bound with both leading and trailing forward slashes.
2. When refreshing freeze.py with changes to routes.py, the leading 'app/' must be removed from every reference to an external files (e.g., markdown content files) 

### Conda and PIP
1. If you primarily use conda for virtual environments and package management, you may encounter issue with frozen flask. The only solution at the moment requires editing the package source
files, which is ill-advised. Fortunately, the same problems have not been encountered when using the package manager, PIP, and a native python virtual environment. 

#### Contact
Ben Norton
ben.norton@yale.edu
