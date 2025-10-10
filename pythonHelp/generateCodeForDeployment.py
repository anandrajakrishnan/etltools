import sys
import os
import yaml
#
def loadParamResolver() -> dict:
    # read param resolver file
    with open('./envParams.yaml') as paramFile:
        paramData = yaml.safe_load(paramFile)
        return paramData
#
def replaceString(data:str, conversionParam:dict) -> str:
    for eachKey in conversionParam:
        data = data.replace('~' + eachKey + '~', conversionParam[eachKey])
    return data
def renderFile(fileLocation) -> None:
    with open(fileLocation, 'r') as inFile:
        firstLine = inFile.readline()
        if (fileLocation.endswith('.sql') and firstLine == '--Snowflake\n') or \
            (fileLocation.endswith('.py') and firstLine == '# Snowflake\n'):
            conversionParam = paramData['environment']['snowflake'][renderForEnvironment]
            for eachLine in inFile:
                print(replaceString(eachLine, conversionParam), end='')
        else:
            print(f'First line should have the source name: {firstLine}')
            exit(1)
    #print()
#
def renderFolder(folderLocation) -> None:
    for eachFile in os.listdir(folderLocation):
        fullPath = os.path.join(folderLocation, eachFile)
        if eachFile.endswith('.sql'):
            renderFile(fullPath)
#
if __name__ == '__main__':
    if len(sys.argv) != 3:
        print(f'missing parameters {sys.argv}')
        exit(1)
    #
    fileToBeRendered = sys.argv[1]
    renderForEnvironment = sys.argv[2]
    if renderForEnvironment not in ('DEV', 'QA', 'UAT', 'PROD'):
        print(f'incorrect environment: {renderForEnvironment}')
        exit(1)
    #
    if not os.path.exists(fileToBeRendered):
        print(f'File doesn\'t exist: {fileToBeRendered}')
        exit(1)
    #
    # read param resolver file
    paramData = loadParamResolver()
    #
    if os.path.isfile(fileToBeRendered):
        renderFile(fileToBeRendered)
    elif os.path.isdir(fileToBeRendered):
        renderFolder(fileToBeRendered)
    else:
        print(f'input is not a file nor a folder: {fileToBeRendered}')
        exit(1)
    #
