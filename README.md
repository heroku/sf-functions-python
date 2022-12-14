# sf-functions-python

Python support for [Salesforce Functions](https://developer.salesforce.com/docs/platform/functions/overview).

> Note: This feature is in beta and has been released early so we can collect feedback. It may contain significant problems, undergo major changes, or be discontinued. The use of this feature is governed by the Salesforce.com Program Agreement.

---

# Getting Started with Python for Functions

## Prerequisites

> Any install commands that follow assume a Mac OSX system with Homebrew available.  If you’re on another OS you’ll have to click through the links to get alternative install instructions.

### [Install Python 3](https://www.python.org/downloads/)

```sh
brew install python3
```

The installed Python version should be at least `3.10.6` or higher  

You can check this with `python3 --version`

> On some machines it’s necessary to run Python and Pip commands using python3 or pip3 which point to the Homebrew-managed Python interpreter versus running python or pip which tends to point at the system installed Python interpreter.  

### [Install Git](https://git-scm.com/downloads)

```sh
brew install git
```

The installed Git version should be at least `2.36.0` or higher

You can check this with `git --version`

### [Install / Update the Salesforce CLI](https://developer.salesforce.com/docs/atlas.en-us.sfdx_setup.meta/sfdx_setup/sfdx_setup_install_cli_rc.htm)

If you haven’t already installed the Salesforce CLI, follow 
[these steps](https://developer.salesforce.com/docs/atlas.en-us.sfdx_setup.meta/sfdx_setup/sfdx_setup_install_cli.htm). 

If you already have the Salesforce CLI installed, make sure it is updated to the latest release, which contains the Python 
functions support:

```sh
sfdx update
```

This will update both the sfdx and sf commands.  Verify that:

* `sf --version` is `1.57.0` (or higher)
* `sfdx --version` is `7.180.0` (or higher)

### [Create a SFDX Project](https://developer.salesforce.com/docs/platform/functions/guide/create-dx-project.html)

Functions must be located within a SFDX project so let’s create one.  

```sh
sf generate project -n PythonFunctionsAlpha
```

Some of the following commands need to be run from within the SFDX project directory so change into that directory now with

```sh
cd PythonFunctionsAlpha
```

You should also edit the `config/project-scratch-def.json` file to include the **`Functions`** feature.  After modification, your 
file should look similar to the following:

```json
{
  "orgName": "SomeOrgName",
  "edition": "Developer",
  "features": ["EnableSetPasswordInApi", "Functions"],
  "settings": {
    "lightningExperienceSettings": {
      "enableS1DesktopEnabled": true
    },
    "mobileSettings": {
      "enableS1EncryptedStoragePref2": false
    }
  }
}
```

The above is needed for connecting and deploying Functions in scratch orgs which is 
[the recommended workflow](https://developer.salesforce.com/docs/platform/functions/guide/connect-dev-org.html) when working 
with Functions.

And, to deploy any Salesforce Function, your SFDX project needs to be a git repo.  This is because the deployment process 
uses git tracked changes to figure out what to deploy.  Run the following commands to setup git:

```sh
git init
```

> It is not a requirement to push your code to GitHub or any other code hosting site.  Committing locally will work fine for deploying.  

### Connect Your Org

You’ll need to configure your Salesforce org to develop and invoke Salesforce Functions. Develop your functions in scratch 
orgs with Dev Hub or in sandbox orgs.  Follow the steps on 
[this page](https://developer.salesforce.com/docs/platform/functions/guide/configure_your_org.html) to ensure everything 
is setup correctly first.

Once your Org is configured you can login and set it as the default Dev Hub with the following command:

```sh
sf login org --alias PythonOrg --set-default-dev-hub --set-default
```

This will make **PythonOrg** the default Dev Hub for subsequent commands.

Then create a scratch org:

```sh
sfdx force:org:create \
  --definitionfile config/project-scratch-def.json \
  --setalias PythonScratch \
  --setdefaultusername
```

This will make it so that, when you run a Function, it will connect to and use the **PythonScratch** org.

### Connect Your Compute Environment

Login to Salesforce Functions with the same credentials you used to connect your Dev Hub org.

```sh
sf login functions
```

Then you will be able to create the compute environment and associate it with the **PythonScratch** org we created while
connecting your org.

```sh
sf env create compute \
  --connected-org PythonScratch \
  --alias PythonCompute
```

This will make it so that, when you deploy a Function, it will be deployed to the *PythonCompute* environment linked to 
your scratch org.

## Create and Run a Python Function Locally

### Generate the Python Function

From the SFDX project root, run:

```sh
sf generate function \
  --language python \
  --function-name hellopython
```

The remaining commands will be executed within the newly generated project folder change to that folder by running

```sh
cd functions/hellopython
```

### Create the Python [Virtual Environment](https://docs.python.org/3/library/venv.html#creating-virtual-environments) & Install Dependencies

```sh
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

This will ensure your function has all dependencies it requires installed before you run it.  If you forgot to do this 
before starting the Function locally you’ll receive an error reminding you to perform this step.

### Run the Python Function Locally

```sh
sf run function start
```

This will start the function running locally on http://localhost:8080.  Messages logged by the running function will appear here.

### Invoke the Running Python Function

After starting the function:

* open a new command line terminal 
* navigate to the `hellopython` directory 
* invoke the function by sending it a payload

```sh
sf run function --function-url http://localhost:8080 --payload '{}'
```

## Deploy the Python Function

The following commands need to be executed from the **root of your SFDX project** so change into that directory now.

### Commit your changes to Git

All code changes made to a function will need to be staged and committed before you can deploy.

```sh
git add . 
git commit -m "Trying out python functions"
```

Once everything is committed to git run

```sh
sf deploy functions --connected-org PythonScratch
```

This deployment process may take several minutes.

### Invoke the Function from Apex

The easiest way to invoke the function deployed to our scratch org is with some Apex code.  Generate an Apex class with:

```sh
sfdx force:apex:class:create \
  --classname ApexTrigger \
  --outputdir force-app/main/default/classes
```

Open `force-app/main/default/classes/ApexTrigger.cls` and replace it with the following code:

```java
public with sharing class ApexTrigger {
    public static void runFunction() {
        System.debug('Running hellopython');
        functions.Function fn = functions.Function.get('PythonFunctionsAlpha.hellopython');
        functions.FunctionInvocation invocation = fn.invoke('{}');
        System.debug('Response: ' + invocation.getResponse());
    }
}
```

This code will:

* Lookup the reference to our function using the functions.Function.get method 
* Invoke the function with an empty json payload
* Print the response

Upload this Apex class to your scratch org with

```sh
sfdx force:source:push --targetusername PythonScratch
```

Open a developer console

```sh
sfdx force:org:open -p /_ui/common/apex/debug/ApexCSIPage
```

And execute the function with

```sh
echo "ApexTrigger.runFunction();" | sfdx force:apex:execute -f /dev/stdin
```

The developer console will show a log entry after the function executes which you can double-click to open.  Toggle the 
Debug Only filter to reduce the log messages to just the ones from the ApexTrigger function.  You should see a view like 
the one below:

![Developer Console](./assets/developer-console.png)

---

> NOTE: You may encounter the following error

```
System.CalloutException: Error during Salesforce Functions Sync Invocation. Ensure that 
function 'PythonFunctionsAlpha.hellopython' is deployed and its status is 
available ('OK', 'up'). If issue persists, contact Salesforce Support.
```

If you see this then there may not be a problem, the function just might not be available yet in the compute 
environment. Wait several minutes and then try the command above again.
