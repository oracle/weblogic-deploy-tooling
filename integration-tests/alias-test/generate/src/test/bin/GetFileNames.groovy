def skip = project.properties.skip
if (skip == 'true') {
    println "Execution skipped"
    return
}

def dirName = project.properties.buildDir
def directory = new File(dirName)
if (!directory.isDirectory()) {
    println "The ${directory.getAbsolutePath()} does not exist"
    System.exit(1)
}
println "The ${directory.getAbsolutePath()} exists"

def onlineFiles = []
directory.eachFileMatch(~/generatedOnline.*\.json/) {
    onlineFiles << it.name
}

if (onlineFiles.size() > 0) {
    println "Setting Maven project property alias-test-generated-online-file-name to ${onlineFiles[0]}"
    project.properties.setProperty("alias-test-generated-online-file-name", onlineFiles[0])
}

def offlineFiles = []
directory.eachFileMatch(~/generatedOffline.*\.json/) {
    offlineFiles << it.name
}

if (offlineFiles.size() > 0) {
    println "Setting Maven project property alias-test-generated-offline-file-name to ${offlineFiles[0]}"
    project.properties.setProperty("alias-test-generated-offline-file-name", offlineFiles[0])
}
