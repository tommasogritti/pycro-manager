"""
This script reads the versions of pycromanager and its dependencies from the pom file 
and makes updates to the micro-manager ivy.xml file

"""

import xml.etree.ElementTree as ET
from semantic_version import Version
from pathlib import Path
import requests


def read_versions(root):
    versions = {}
    versions['PycroManagerJava'] = Version(root.find("version").text)
    # iterate through the dependencies and get NDTiff, NDViewer, and AcqEngJ
    dependencies = root.findall(".//dependency")
    for dependency in dependencies:
        artifactId = dependency.find("artifactId").text
        version = dependency.find("version").text
        if artifactId in ["NDTiffStorage", "NDViewer", "AcqEngJ"]:
            versions[artifactId] = Version(version)
    return versions

git_repos_dir = Path(__file__).parent.parent.parent
ivy_path = git_repos_dir + '/micro-manager/buildscripts/ivy.xml'
  
# Read from pom.xml in pycromanager
f = str(git_repos_dir) + '/pycro-manager/java/pom.xml'
tree = ET.parse(f)
root = tree.getroot()

updated_versions = read_versions(root)


tree = ET.parse(ivy_path)
root = tree.getroot()

dependencies = {
    "org.micro-manager.ndviewer": {"name":"NDViewer"},
    "org.micro-manager.acqengj": {"name":"AcqEngJ"},
    "org.micro-manager.ndtiffstorage": {"name":"NDTiffStorage"},
    "org.micro-manager.pycro-manager": {"name":"PycroManagerJava"},
}



for dependency in root.iter("dependency"):
    if "org" not in dependency.attrib:
        continue
    org = dependency.attrib["org"]
    name = dependency.attrib["name"]
    if org in dependencies and name == dependencies[org]["name"]:
        new_version = str(updated_versions[dependencies[org]["name"]])
        print(dependencies[org]["name"], '\t', dependency.attrib["rev"],  'to\t', new_version)
        dependency.attrib["rev"] = new_version


tree.write(ivy_path)



# Wait for PycroManagerJava to become available, because there is a delay after it is deployed
dep_name = 'PycroManagerJava'
latest_version_number = str(updated_versions[dep_name])
url = f"https://s01.oss.sonatype.org/service/local/repositories/releases/content/org/micro-manager/{dep_name.lower()}/{dep_name}/{latest_version_number}/{dep_name}-{latest_version_number}.jar"

start = time.time()
while True:
    response = requests.head(url)
    if response.status_code == 200:
        break
    else:
        print(f"waiting for {dep_name}-{latest_version_number} for {time.time() - start} s\r", end='')
        time.sleep(5)
print('Dependency available')
