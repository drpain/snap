#!/usr/bin/env python
import subprocess, time, sys, urllib, json, os, shutil
from serve import *

print "Starting Snap"
print "Starting individual processes of PhantomJS to handle each breakpoint"

# List of test URLs, provided as arguments
urlToCheck = []

# Allow the url's to be provided via arguments to the call
if len(sys.argv) > 1:
    sys.argv.pop(0)
    for arg in sys.argv:
        try:
            urllib.urlopen(arg)
        except IOError as e:
            print "ERROR: Invalid URL provided as argument ["+str(arg)+"]", e
            exit(1)
        urlToCheck.append(arg)

# Fallback
if len(urlToCheck) == 0:
    print "ERROR: No urls to test";
    exit(1)

# The BS3 breakpoints I want to see + 320px (regarded as true min screen width)
# It hasn't been tested until it's been tested on an iPhone 4
breakPoints = [
    320,
    480,
    768,
    992,
    1200
]

# Other variables for this to work
startTime = int(time.time())
screenShotPath = "screenshots"
abspath = os.path.abspath(__file__)
pwd = os.path.dirname(abspath)

# JSON configuration, needed for Angular
configuration = {
    'startTime': startTime,
    'rendered': {}
}

def updateLinks():
    global screenShotPath, startTime
    configurationPath = os.path.join(str(screenShotPath), str(startTime))
    links = {}

    # If the links exist, try and read it
    if os.path.exists(os.path.join(screenShotPath, "links.json")):
        source = open(os.path.join(screenShotPath, "links.json"),'r+')
        getLinks = source.read()
        source.close()
        if len(getLinks) > 0:
            links = json.loads(getLinks)

    thisRun = {
        startTime: {
            'label': startTime,
            'href': configurationPath
        }
    }

    links.update(thisRun)
    destination = open(os.path.join(screenShotPath, "links.json"),'w')
    json.dump(links, destination, indent=2, sort_keys=True)
    destination.close()
    return True


def copyTemplate():
    global screenShotPath, pwd

    source = os.path.join(pwd, 'favicon.ico')
    destination = os.path.join(pwd, screenShotPath, 'favicon.ico')
    shutil.copyfile(source, destination)

    source = os.path.join(pwd, 'template.html')
    destination = os.path.join(pwd, screenShotPath, 'index.html')
    shutil.copyfile(source, destination)
    return True


def createConfiguration():
    global configuration, screenShotPath, startTime
    print "Generating configuration file (JSON)"
    configurationPath = os.path.join(str(screenShotPath), str(startTime))
    os.mkdir(configurationPath, 0755);
    file = open(os.path.join(configurationPath, "config.json"),'w')
    file.write(json.dumps(configuration, indent=2, sort_keys=True))
    file.close()

    # Update the list of JSON links
    updateLinks()

    # Copy the template into the screenshots folder
    copyTemplate()

    # Start the webserver
    subprocess.call(['google-chrome', 'http://localhost:5000'])
    StartServer(PORT=5000)


def generateShot(url, width):
    global startTime, screenShotPath, configuration

    # Build up the output name
    namedUrl = url.replace("http://", "")
    namedUrl = namedUrl.replace("https://", "")
    namedUrl = namedUrl.replace("/", "--")
    outputUrl = str(startTime)+"/"+str(width)+"/"+namedUrl+".png"
    outputName = screenShotPath+"/"+outputUrl

    # Optional cookie to be set
    cookies = json.dumps({
        'rbViewed' : "%7B%22rbViewed%22%3A%221%22%2C%22lastViewed%22%3A%20%221442385836270%22%2C%20%22threeDaysOrMore%22%3A%20%22false%22%7D"
    })

    # Determine the device height from the width
    # Portrait for smaller devices, landscape for larger devices
    if width < 800:
        height = int(width * 1.5)
    else:
        height = int(width * 0.8)

    # Command and params to be passed through
    command = [
        'phantomjs',
        'render.js',
        str(url),
        str(width),
        str(height),
        outputName,
        cookies,
    ]

    # Add the configuration for the individual screenshots
    if configuration['rendered'].has_key(str(url)) == False:
        configuration['rendered'][str(url)] = [];

    configuration['rendered'][str(url)].append({
        str(width): {
            'width': width,
            'height': height,
            'src': outputUrl
        }
    });

    # Fire and Forget
    subprocess.Popen(command)

    # Synchronous Command
    # try:
    #     print " ".join(command)
    #     retcode = subprocess.call(" ".join(command), shell=True)
    #     if retcode < 0:
    #         print >>sys.stderr, "Child was terminated by signal", -retcode
    #     else:
    #         print >>sys.stderr, "Success"
    # except OSError as e:
    #     print >>sys.stderr, "Execution failed:", e

    print "Queued Screenshot FOR:", url, "WIDTH:", width, "HEIGHT:", height
    return True


def shotQueue(currentBp=None, currentUrl=None):
    global breakPoints, urlToCheck
    start = breakPoints[0];
    end = breakPoints[-1];

    # First iteration
    if currentBp is None and currentUrl is None:
        currentBp = start
        currentUrl = urlToCheck[0]
        urlToCheck = urlToCheck[1:]

    # Prevent out of bound recursion. Exit when done - THE END
    elif len(urlToCheck) == 0 and currentBp == end:
        print "Queued, awaiting response"
        createConfiguration()

    # Still busy with Break Points for URL
    elif currentBp < end:
        currentBp = breakPoints[breakPoints.index(currentBp)+1]

    # Done with current URL
    elif currentBp == end:
        currentBp = start
        currentUrl = urlToCheck[0]
        urlToCheck = urlToCheck[1:]

    # Generate the Screenshot man
    generateShot(currentUrl, currentBp)

    # Recurse back with the next iteration details
    return shotQueue(currentBp, currentUrl)

# Start it all
shotQueue()
