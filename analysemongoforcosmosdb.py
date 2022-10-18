#!/usr/bin/python3
# code made by emmanuel deletang 
# code free to use to find mongo API compatibility for migration to cosmosdb 4.0 or 4.2 
# The format of the command is:
# python .\analysemongoforcosmosdb.py --directory full-path-to-directory-to-scan



import glob
import pathlib
import os
import sys
import re
import argparse


versions = ['4.0','4.2']
processingFeedbackLines = 5000
issuesDict = {}
detailedIssuesDict = {}
supportedDict = {}
skippedFileList = []
exceptionFileList = []
numProcessedFiles = 0


def double_check(checkOperator, checkLine, checkLineLength):
    foundOperator = False
    
    for match in re.finditer(re.escape(checkOperator), checkLine):
        if (match.end() == checkLineLength) or (not checkLine[match.end()].isalpha()):
            foundOperator = True
            break
    
    return foundOperator


def scan_code(args, keywords):
    global numProcessedFiles, issuesDict, detailedIssuesDict, supportedDict, skippedFileList, exceptionFileList
    
    ver = args.version

    usage_map = {}
    cmd_map = {}
    line_ct = 0
    totalLines = 0
    
    # create the file or list of files
    fileArray = []
    
    includedExtensions = []
    if args.includedExtensions != "ALL":
        includedExtensions = args.includedExtensions.lower().split(",")
    excludedExtensions = []
    if args.includedExtensions != "NONE":
        excludedExtensions = args.excludedExtensions.lower().split(",")
    
    if args.scanFile is not None:
        fileArray.append(args.scanFile)
        numProcessedFiles += 1
    else:
        for filename in glob.iglob("{}/**".format(args.scanDir), recursive=True):
            if os.path.isfile(filename):
                if ((pathlib.Path(filename).suffix[1:].lower() not in excludedExtensions) and
                     ((args.includedExtensions == "ALL") or 
                      (pathlib.Path(filename).suffix[1:].lower() in includedExtensions))):
                    fileArray.append(filename)
                    numProcessedFiles += 1
                else:
                    skippedFileList.append(filename)
                    
    for thisFile in fileArray:
        print("processing file {}".format(thisFile))
        with open(thisFile, "r") as code_file:
            # line by line technique
            try:
                fileLines = code_file.readlines()
            except:
                print("  exception reading file, skipping")
                exceptionFileList.append(thisFile)
                continue
                
            fileLineNum = 1
            
            for lineNum, thisLine in enumerate(fileLines):
                thisLineLength = len(thisLine)
                
                for checkCompat in keywords:
                    if (keywords[checkCompat][ver] == 'No'):
                        # only check for unsupported operators
                        if (thisLine.find(checkCompat) >= 0):
                            # check for false positives - for each position found see if next character is not a..z|A..Z or if at EOL
                            if double_check(checkCompat, thisLine, thisLineLength):
                                # add it to the counters
                                if checkCompat in issuesDict:
                                    issuesDict[checkCompat] += 1
                                else:
                                    issuesDict[checkCompat] = 1
                                # add it to the filenames/line-numbers
                                if checkCompat in detailedIssuesDict:
                                    if thisFile in detailedIssuesDict[checkCompat]:
                                        detailedIssuesDict[checkCompat][thisFile].append(fileLineNum)
                                    else:
                                        detailedIssuesDict[checkCompat][thisFile] = [fileLineNum]
                                else:
                                    detailedIssuesDict[checkCompat] = {}
                                    detailedIssuesDict[checkCompat][thisFile] = [fileLineNum]

                    elif (keywords[checkCompat][ver] == 'Yes') and args.showSupported:
                        # check for supported operators
                        if (thisLine.find(checkCompat) >= 0):
                            # check for false positives - for each position found see if next character is not a..z|A..Z or if at EOL
                            if double_check(checkCompat, thisLine, thisLineLength):
                                if checkCompat in supportedDict:
                                    supportedDict[checkCompat] += 1
                                else:
                                    supportedDict[checkCompat] = 1
                                
                if (fileLineNum % processingFeedbackLines) == 0:
                    print("  processing line {}".format(fileLineNum))
                fileLineNum += 1
        

def main(args):
    parser = argparse.ArgumentParser(description="Parse the command line.")
    parser.add_argument("--v", dest="version", action="store", default="4.2", help="Cosmosdb mongo API version (default 4.2)", choices=versions, required=False)
    parser.add_argument("--d", dest="scanDir", action="store", help="Directory for files to scan for compatibility", required=False)
    parser.add_argument("--f", dest="scanFile", action="store", help="Specific file to scan for compatibility", required=False)
    parser.add_argument("--O", dest="OUTFILE", action="store", help="Specific file to WRITE THE UNCOMPATIBILITY", required=False)
    parser.add_argument("--excluded-extensions", dest="excludedExtensions", action="store", default="NONE", help="Filename extensions to exclude from scanning, comma separated", required=False)
    parser.add_argument("--included-extensions", dest="includedExtensions", action="store", default="ALL", help="Filename extensions to include in scanning, comma separated", required=False)
    parser.add_argument("--show-supported", dest="showSupported", action="store_true", default=False, help="Include supported operators in the scan", required=False)
    args = parser.parse_args()
    
    if args.scanDir is None and args.scanFile is None:
        parser.error("at least one of --d and --f required")

    elif args.scanDir is not None and args.scanFile is not None:
        parser.error("must provide exactly one of --d or --f required, not both")
    
    elif args.scanFile is not None and not os.path.isfile(args.scanFile):
        parser.error("unable to locate file {}".format(args.scanFile))
    
    elif args.scanDir is not None and not os.path.isdir(args.scanDir):
        parser.error("unable to locate directory {}".format(args.scanDir))
        
    keywords = load_keywords()
    scan_code(args, keywords)
    
    print("")
    print("Processed {} files, skipped {} files".format(numProcessedFiles,len(skippedFileList)+len(exceptionFileList)))
    OUT = format(args.OUTFILE) +".txt"
    if len(issuesDict) > 0:
        f = open(OUT, "a")
        f.write(" please find in the file  the uncompatibility find ")
        f.write("\n")
              
        print("")
        

        print("The following {} unsupported operators were found".format(len(issuesDict)))
        f.write("The following {} unsupported operators were found".format(len(issuesDict)))
        f.write("\n")
        
        for thisKeyPair in sorted(issuesDict.items(), key=lambda x: (-x[1],x[0])):
            print("  {} | found {} time(s)".format(thisKeyPair[0],thisKeyPair[1]))
            f.write("  {} | found {} time(s)".format(thisKeyPair[0],thisKeyPair[1]))
            f.write("\n")
        
            
        # output detailed unsupported operator findings
        print("")
        f.write("\n")
        
        print("Unsupported operators by filename and line number")
        for thisKeyPair in sorted(issuesDict.items(), key=lambda x: (-x[1],x[0])):
            f.write("  {} | lines = found {} time(s)".format(thisKeyPair[0],thisKeyPair[1]))
            f.write("\n")
            print("  {} | lines = found {} time(s)".format(thisKeyPair[0],thisKeyPair[1]))
            for thisFile in detailedIssuesDict[thisKeyPair[0]]:
                f.write("    {} | lines = {}".format(thisFile,detailedIssuesDict[thisKeyPair[0]][thisFile]))
                f.write("\n")
                print("    {} | lines = {}".format(thisFile,detailedIssuesDict[thisKeyPair[0]][thisFile]))
        f.close

    else:
        f = open(OUT, "a")
        print("")
        print("No unsupported operators found")
        f.write("No unsupported operators found")
        f.close

    if len(supportedDict) > 0 and args.showSupported:
        print("")
        print("The following {} supported operators were found".format(len(supportedDict)))
        for thisKeyPair in sorted(supportedDict.items(), key=lambda x: (-x[1],x[0])):
            print("  - {} | found {} time(s)".format(thisKeyPair[0],thisKeyPair[1]))

    if len(skippedFileList) > 0:
        print("")
        print("List of skipped files - excluded extensions")
        for skippedFile in skippedFileList:
            print("  {}".format(skippedFile))

    if len(exceptionFileList) > 0:
        print("")
        print("List of skipped files - unsupported file type/content")
        for exceptionFile in exceptionFileList:
            print("  {}".format(exceptionFile))

    print("")

    if len(issuesDict) > 0:
        sys.exit(1)
    else:
        sys.exit(0)

## list of keyword to maintain or add 
##
##
##

def load_keywords():
    thisKeywords = {
     "$abs":{"mongodbversion":"4.2","4.0":"No","4.2":"Yes"},
 "$delete":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$eval":{"mongodbversion":"4.0","4.0":"Yes","4.2":"No"},
 "$find":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$findAndModify":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$getLastError":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$getMore":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$getPrevError":{"mongodbversion":"4.0","4.0":"No","4.2":"No"},
 "$insert":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$parallelCollectionScan":{"mongodbversion":"4.0","4.0":"No","4.2":"No"},
 "$resetError":{"mongodbversion":"4.0","4.0":"No","4.2":"No"},
 "$update":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$abortTransaction":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$commitTransaction":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$authenticate":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$getnonce":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$logout":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$cloneCollectionAsCapped":{"mongodbversion":"4.0","4.0":"No","4.2":"No"},
 "$collMod":{"mongodbversion":"4.0","4.0":"No","4.2":"No"},
 "$connectionStatus":{"mongodbversion":"4.0","4.0":"No","4.2":"No"},
 "$convertToCapped":{"mongodbversion":"4.0","4.0":"No","4.2":"No"},
 "$copydb":{"mongodbversion":"4.0","4.0":"No","4.2":"No"},
 "$create":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$createIndexes":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$currentOp":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$drop":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$dropDatabase":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$dropIndexes":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$filemd5":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$killCursors":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$killOp":{"mongodbversion":"4.0","4.0":"Yes","4.2":"No"},
 "$listCollections":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$listDatabases":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$listIndexes":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$reIndex":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$renameCollection":{"mongodbversion":"4.0","4.0":"No","4.2":"No"},
 "$buildInfo":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$collStats":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$connPoolStats":{"mongodbversion":"4.0","4.0":"No","4.2":"No"},
 "$connectionStatus":{"mongodbversion":"4.0","4.0":"No","4.2":"No"},
 "$dataSize":{"mongodbversion":"4.0","4.0":"No","4.2":"No"},
 "$dbHash":{"mongodbversion":"4.0","4.0":"No","4.2":"No"},
 "$dbStats":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$explain":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$features":{"mongodbversion":"4.0","4.0":"No","4.2":"No"},
 "$hostInfo":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$listDatabases":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$listCommands":{"mongodbversion":"4.0","4.0":"No","4.2":"No"},
 "$profiler":{"mongodbversion":"4.0","4.0":"No","4.2":"No"},
 "$serverStatus":{"mongodbversion":"4.0","4.0":"No","4.2":"No"},
 "$top":{"mongodbversion":"4.0","4.0":"No","4.2":"No"},
 "$whatsmyuri":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$aggregate":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$count":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$distinct":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$mapReduce":{"mongodbversion":"4.0","4.0":"No","4.2":"No"},
 "$addFields":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$bucket":{"mongodbversion":"4.0","4.0":"No","4.2":"No"},
 "$bucketAuto":{"mongodbversion":"4.0","4.0":"No","4.2":"No"},
 "$changeStream":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$collStats":{"mongodbversion":"4.0","4.0":"No","4.2":"No"},
 "$count":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$currentOp":{"mongodbversion":"4.0","4.0":"No","4.2":"No"},
 "$facet":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$geoNear":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$graphLookup":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$group":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$indexStats":{"mongodbversion":"4.0","4.0":"No","4.2":"No"},
 "$limit":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$listLocalSessions":{"mongodbversion":"4.0","4.0":"No","4.2":"No"},
 "$listSessions":{"mongodbversion":"4.0","4.0":"No","4.2":"No"},
 "$lookup":{"mongodbversion":"4.0","4.0":"No","4.2":"Partial"},
 "$match":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$merge":{"mongodbversion":"4.2","4.0":"No","4.2":"Yes"},
 "$out":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$planCacheStats":{"mongodbversion":"4.2","4.0":"No","4.2":"Yes"},
 "$project":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$redact":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$regexFind":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$regexFindAll":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$regexMatch":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$replaceRoot":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$replaceWith":{"mongodbversion":"4.0","4.0":"No","4.2":"Yes"},
 "$sample":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$set":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$skip":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$sort":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$sortByCount":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$unset":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$unwind":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$and":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$not":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$or":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$convert":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$toBool":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$toDate":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$toDecimal":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$toDouble":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$toInt":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$toLong":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$toObjectId":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$toString":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$setEquals":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$setIntersection":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$setUnion":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$setDifference":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$setIsSubset":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$anyElementTrue":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$allElementsTrue":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$cmp":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$eq":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$gt":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$gte":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$lt":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$lte":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$ne":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$in":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$nin":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$abs":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$add":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$ceil":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$divide":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$exp":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$floor":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$ln":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$log":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$log10":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$mod":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$multiply":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$pow":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$round":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$sqrt":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$subtract":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$trunc":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$acos":{"mongodbversion":"4.0","4.0":"No","4.2":"Yes"},
 "$acosh":{"mongodbversion":"4.0","4.0":"No","4.2":"Yes"},
 "$asin":{"mongodbversion":"4.0","4.0":"No","4.2":"Yes"},
 "$asinh":{"mongodbversion":"4.0","4.0":"No","4.2":"Yes"},
 "$atan":{"mongodbversion":"4.0","4.0":"No","4.2":"Yes"},
 "$atan2":{"mongodbversion":"4.0","4.0":"No","4.2":"Yes"},
 "$atanh":{"mongodbversion":"4.0","4.0":"No","4.2":"Yes"},
 "$cos":{"mongodbversion":"4.0","4.0":"No","4.2":"Yes"},
 "$cosh":{"mongodbversion":"4.0","4.0":"No","4.2":"Yes"},
 "$degreesToRadians":{"mongodbversion":"4.0","4.0":"No","4.2":"Yes"},
 "$radiansToDegrees":{"mongodbversion":"4.0","4.0":"No","4.2":"Yes"},
 "$sin":{"mongodbversion":"4.0","4.0":"No","4.2":"Yes"},
 "$sinh":{"mongodbversion":"4.0","4.0":"No","4.2":"Yes"},
 "$tan":{"mongodbversion":"4.0","4.0":"No","4.2":"Yes"},
 "$tanh":{"mongodbversion":"4.0","4.0":"No","4.2":"Yes"},
 "$concat":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$indexOfBytes":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$indexOfCP":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$ltrim":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$rtrim":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$trim":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$split":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$strLenBytes":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$strLenCP":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$strcasecmp":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$substr":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$substrBytes":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$substrCP":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$toLower":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$toUpper":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$meta":{"mongodbversion":"4.0","4.0":"No","4.2":"No"},
 "$arrayElemAt":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$arrayToObject":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$concatArrays":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$filter":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$indexOfArray":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$isArray":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$objectToArray":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$range":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$reverseArray":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$reduce":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$size":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$slice":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$zip":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$in":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$map":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$let":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$$$CLUSTERTIME":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$$$CURRENT":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$$$DESCEND":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$$$KEEP":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$$$NOW":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$$$PRUNE":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$$$REMOVE":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$$$ROOT":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$literal":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$dayOfYear":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$dayOfMonth":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$dayOfWeek":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$year":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$month":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$week":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$hour":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$minute":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$second":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$millisecond":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$dateToString":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$isoDayOfWeek":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$isoWeek":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$dateFromParts":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$dateToParts":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$dateFromString":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$isoWeekYear":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$cond":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$ifNull":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$switch":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$type":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$sum":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$avg":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$first":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$last":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$max":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$min":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$push":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$addToSet":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$stdDevPop":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$stdDevSamp":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$mergeObjects":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$or":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$and":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$not":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$nor":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$exists":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$type":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$expr":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$jsonSchema":{"mongodbversion":"4.0","4.0":"No","4.2":"No"},
 "$mod":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$regex":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$text":{"mongodbversion":"4.0","4.0":"Yes","4.2":"No"},
 "$where":{"mongodbversion":"4.0","4.0":"No","4.2":"No"},
 "$all":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$elemMatch":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$size":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$comment":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$elemMatch":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$meta":{"mongodbversion":"4.0","4.0":"No","4.2":"No"},
 "$slice":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$inc":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$mul":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$rename":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$setOnInsert":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$set":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$unset":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$min":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$max":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$currentDate":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$$":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$$[]":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$$[\<identifier\>]":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$addToSet":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$pop":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$pullAll":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$pull":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$push":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$pushAll":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$each":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$slice":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$sort":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$position":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$bit":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$bitsAllSet":{"mongodbversion":"4.0","4.0":"No","4.2":"No"},
 "$bitsAnySet":{"mongodbversion":"4.0","4.0":"No","4.2":"No"},
 "$bitsAllClear":{"mongodbversion":"4.0","4.0":"No","4.2":"No"},
 "$bitsAnyClear":{"mongodbversion":"4.0","4.0":"No","4.2":"No"},
 "$$geoWithin":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$$geoIntersects":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$$near":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$$nearSphere":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$$geometry":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$$minDistance":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$$maxDistance":{"mongodbversion":"4.0","4.0":"Yes","4.2":"Yes"},
 "$$center":{"mongodbversion":"4.0","4.0":"No","4.2":"No"},
 "$$centerSphere":{"mongodbversion":"4.0","4.0":"No","4.2":"No"},
 "$$box":{"mongodbversion":"4.0","4.0":"No","4.2":"No"},
 "$$polygon":{"mongodbversion":"4.0","4.0":"No","4.2":"No"}}
        
    return thisKeywords

    
if __name__ == '__main__':
    main(sys.argv[1:])
