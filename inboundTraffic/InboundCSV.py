'''
Created on Oct 12, 2020

@author: {ANAND.RAJAKRISHNAN2@vnsny.org}
'''
from inboundTraffic import InboundMaster as IM
from os import path,listdir,remove,rename
import glob,shutil
import csv
from datetime import datetime
import concurrent.futures
from postgreop import DBOperations,DASADMINprofile,JMANprofile
from inboundTraffic.SQLstatements import SELECT_COL_LIST,INSERT_WHITE_LIST,INSERT_FEEDCOUNT
from inboundTraffic.SQLstatements import UPDATE_WHITE_LIST,UPDATE_FEEDCOUNT,GET_COLUMN_SK_COUNT
#
class InboundCSV(IM.InboundCom):
    def __init__(self,jobId,DAScolsDict,headerRows,encoding='latin_1',conversionTable={},fileDelimiter=',',lineSep='\r\n',escapechar=None,transformation=None):
        self.__DAScolsName=[]
        self.__DAScolsType=[]
        self.__headerRows=headerRows
        self.__encoding=encoding
        self.__conversionTable=conversionTable
        self.__fileDelimiter=fileDelimiter
        self.__lineSep=lineSep
        self.__escapechar=escapechar
        self.__transformation=transformation
        # self.__addTStoArchive=addTStoArchive
        self.__currTime=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        super().__init__(jobId)
#
        # DAScolsDict has all DAS columns like JOB_RUN_ID, SYS_UPD_TS etc.
        # These columns are to be handled spearately as they don't come in
        # the input files. These are to be built using separate logic
        for key,value in DAScolsDict.items():
            self.__DAScolsName.append(key)
            self.__DAScolsType.append(value)
#
    def getColumnIter(self,tableSchema,tableName,cur):
        cur.execute(SELECT_COL_LIST,(tableName,tableSchema,tuple(self.__DAScolsName)))
        colIter=[]
        for eachCol in cur:
            colIter.append(eachCol[0])
        colIter.extend(self.__DAScolsName)
        return colIter
#
    def moveIncomingToIPFDIR(self):
        for eachsrcfileList in self._InboundCom__fileprocessList:
            print(eachsrcfileList,self._InboundCom__incomingFileLoc,self._InboundCom__sqlload,sep=',')
            for eachsrcFile in eachsrcfileList[2]:
                shutil.move(path.join(self._InboundCom__incomingFileLoc,eachsrcFile), self._InboundCom__sqlload)
        
#
    def ETLtransform(self,fileObj,sKey=None):
#
        if self._InboundCom__jobId=='LOAD_MEDITURE_FULL_REFRESH':
            csvIter=csv.reader((line.replace('\0','').replace('\\n',' ').replace('\\r',' ') for line in fileObj),delimiter=self.__fileDelimiter,quoting=csv.QUOTE_ALL,quotechar='"',escapechar=self.__escapechar)
            DASdata=''
            for eachValue in self.__DAScolsType:
                if eachValue=='jobRunId':
                    DASdata+=chr(31)+str(self._InboundCom__jobRunID)
                elif eachValue=='timestamp':
                    DASdata+=chr(31)+self.__currTime
            for _ in range(self.__headerRows):
                next(csvIter)
            for eachLine in csvIter:
                if sKey:
                    yield(str(sKey)+chr(31)+chr(31).join(eachLine).translate(self.__conversionTable)+DASdata+'\n')
                    sKey+=1
                else:
                    yield(chr(31).join(eachLine).translate(self.__conversionTable)+DASdata+'\n')
        else:
            csvIter=csv.reader((line.replace('\0','') for line in fileObj),delimiter=self.__fileDelimiter,quoting=csv.QUOTE_ALL,quotechar='"',escapechar=self.__escapechar)
            DASdata=''
            for eachValue in self.__DAScolsType:
                if eachValue=='jobRunId':
                    DASdata+=chr(31)+str(self._InboundCom__jobRunID)
                elif eachValue=='timestamp':
                    DASdata+=chr(31)+self.__currTime
            for _ in range(self.__headerRows):
                next(csvIter)
            for eachLine in csvIter:
                if sKey:
                    yield(str(sKey)+chr(31)+chr(31).join(eachLine).translate(self.__conversionTable)+DASdata+'\n')
                    sKey+=1
                else:
                    yield(chr(31).join(eachLine).translate(self.__conversionTable)+DASdata+'\n')
#
    def ETLtransformCopy(self,fileObj,sKey=None):
#
        if self._InboundCom__jobId=='LOAD_MEDITURE_FULL_REFRESH':
            DASdata=''
            for eachValue in self.__DAScolsType:
                if eachValue=='jobRunId':
                    DASdata+=self.__fileDelimiter+'"'+str(self._InboundCom__jobRunID)+'"'
                elif eachValue=='timestamp':
                    DASdata+=self.__fileDelimiter+'"'+self.__currTime+'"'
            for _ in range(self.__headerRows):
                next(fileObj)
            for eachLine in fileObj:
                if sKey:
                    yield('"'+str(sKey)+'"'+self.__fileDelimiter+eachLine.replace('\\n',' ').replace('\\r',' ')[:-len(self.__lineSep)]+DASdata+'\n')
                    sKey+=1
                else:
                    yield(eachLine.replace('\\n',' ').replace('\\r',' ')[:-len(self.__lineSep)]+DASdata+'\n')
        else:
            DASdata=''
            for eachValue in self.__DAScolsType:
                if eachValue=='jobRunId':
                    DASdata+=self.__fileDelimiter+'"'+str(self._InboundCom__jobRunID)+'"'
                elif eachValue=='timestamp':
                    DASdata+=self.__fileDelimiter+'"'+self.__currTime+'"'
            for _ in range(self.__headerRows):
                next(fileObj)
            for eachLine in fileObj:
                if sKey:
                    yield('"'+str(sKey)+'"'+self.__fileDelimiter+eachLine[:-len(self.__lineSep)]+DASdata+'\n')
                    sKey+=1
                else:
                    yield(eachLine[:-len(self.__lineSep)]+DASdata+'\n')
#
    def bubbleProcess(self,srcfiles):
#
        JMANhandle=DBOperations.DBOperation(JMANprofile)
        JMANconnection=JMANhandle.connOpen()
        JMANcursor=JMANconnection.cursor()
        #Insert into WHITE LIST
        JMANcursor.execute(INSERT_WHITE_LIST,(self._InboundCom__jobRunID,srcfiles[6]))
        JMANconnection.commit()
        #Insert into FEEDFILE
        JMANcursor.execute(INSERT_FEEDCOUNT,(self._InboundCom__jobRunID,srcfiles[4],srcfiles[3],srcfiles[4],))
        JMANconnection.commit()
        #
        DASADMINhandle=DBOperations.DBOperation(DASADMINprofile)
        DASADMINconnection=DASADMINhandle.connOpen()
        DASADMINcur=DASADMINconnection.cursor()
        print('Processing:{}'.format(srcfiles))
        rowCopied=0
        if srcfiles[8] is None:
#
            schemaTable=srcfiles[3]+'.'+srcfiles[4]
            if self.jobType in ['FULL_REFRESH']:
                try:
                    DASADMINcur.execute('TRUNCATE TABLE %s' % schemaTable)
                    maxSK=1
                except DBOperations.DBerror as e:
                    print('Error while truncating table {}'.format(schemaTable))
                    print(str(e))
                    exit(1)
            elif self.jobType in ['APPEND']:
                try:
                    DASADMINcur.execute(GET_COLUMN_SK_COUNT,(srcfiles[3],srcfiles[4],srcfiles[3],srcfiles[4]))
                    if DASADMINcur.rowcount>0:
                        skColumn=DASADMINcur.fetchone()[0]
                        GET_NEXT_SK=DBOperations.sqlHandle.SQL('select coalesce(max( {} ),0)+1 from {}')
                        DASADMINcur.execute(GET_NEXT_SK.format(DBOperations.sqlHandle.Identifier(skColumn,schemaTable)))
                        maxSK=DASADMINcur.fetchone()[0]
                    else:
                        print('No SURROGATE KEY defined for table {}'.format(schemaTable))
                        exit(1)
                except DBOperations.DBerror as e:
                    print('Error while fetching max value of SK for table {}'.format(schemaTable))
                    print(e)
                    exit(1)
#
            for eachFile in srcfiles[2]:
                try:
                    f=open(eachFile,'r',encoding=self.__encoding,newline=self.__lineSep,errors='ignore')
                    objColList=self.getColumnIter(srcfiles[3],srcfiles[4],DASADMINcur)
                    dataIterator=IM.StringIteratorIO((self.ETLtransform(f,maxSK)))
                    DASADMINcur.copy_from(dataIterator,schemaTable,sep=chr(31),size=16384,null='',columns=objColList)
                    rowCopied+=DASADMINcur.rowcount
                    maxSK+=DASADMINcur.rowcount
                    errMessage=None
                    copyStatus='S'
                except Exception as e:
                    errf=open(path.join(self._InboundCom__CEDL_HOME,'etl','Temp',srcfiles[3]+'_'+srcfiles[4]+'.txt'),'w')
                    errf.write('File that caused error:{}'.format(eachFile))
                    errf.write(str(e))
                    errf.close()
                    print(e)
                    f.close()
                    copyStatus='F'
                    rowCopied=0
                    errMessage=str(e)[0:5000]
                dataIterator=None
                f.close()
                DASADMINconnection.commit()
            # copyStatus='S'
            JMANcursor.execute(UPDATE_WHITE_LIST,(copyStatus,rowCopied,rowCopied,srcfiles[6],))
            JMANconnection.commit()
            JMANcursor.execute(UPDATE_FEEDCOUNT,(copyStatus,rowCopied,rowCopied,errMessage,self._InboundCom__jobRunID,srcfiles[4],self._InboundCom__jobRunID,srcfiles[4]))
            JMANconnection.commit()
            DASADMINconnection.close()
            JMANconnection.close()
        else:
            schemaTable=srcfiles[3]+'.'+srcfiles[4]
            if self.jobType in ['FULL_REFRESH']:
                try:
                    DASADMINcur.execute('TRUNCATE TABLE %s' % schemaTable)
                    maxSK=1
                except DBOperations.DBerror as e:
                    print('Error while truncating table {}'.format(schemaTable))
                    print(str(e))
                    exit(1)
            elif self.jobType in ['APPEND']:
                DASADMINcur.execute(GET_COLUMN_SK_COUNT,(srcfiles[3],srcfiles[4],srcfiles[3],srcfiles[4]))
                if DASADMINcur.rowcount>0:
                    skColumn=DASADMINcur.fetchone()[0]
                    GET_NEXT_SK=DBOperations.sqlHandle.SQL('select coalesce(max( {} ),0)+1 from {}')
                    DASADMINcur.execute(GET_NEXT_SK.format(DBOperations.sqlHandle.Identifier(skColumn)))
                    maxSK=DASADMINcur.fetchone()[0]
                else:
                    print('No SURROGATE KEY defined for table {}'.format(schemaTable))
                    exit(1)
            for eachFile in srcfiles[2]:
                try:
                    f=open(eachFile,'r',encoding=self.__encoding,newline=self.__lineSep,errors='ignore')
                    dataIterator=IM.StringIteratorIO((self.ETLtransformCopy(f,maxSK)))
    #                 print(dataIterator.read())
                    DASADMINcur.copy_expert(srcfiles[8],dataIterator)
                    rowCopied+=DASADMINcur.rowcount
                    maxSK+=DASADMINcur.rowcount
                    errMessage=None
                    copyStatus='S'
                except Exception as e:
                    errf=open(path.join(self._InboundCom__CEDL_HOME,'etl','Temp',srcfiles[3]+'_'+srcfiles[4]+'.txt'),'w')
                    errf.write(str(e))
                    errf.close()
                    print(e)
                    f.close()
                    copyStatus='F'
                    rowCopied=0
                    errMessage=str(e)[0:5000]
                    # JMANcursor.execute(UPDATE_WHITE_LIST,(copyStatus,0,0,srcfiles[6],))
                    # JMANconnection.commit()
                    # JMANcursor.execute(UPDATE_FEEDCOUNT,(copyStatus,0,0,str(e)[0:5000],self._InboundCom__jobRunID,srcfiles[4],self._InboundCom__jobRunID,srcfiles[4]))
                    # JMANconnection.commit()
                    # exit(1)
                dataIterator=None
                f.close()
                DASADMINconnection.commit()
            # copyStatus='S'
            JMANcursor.execute(UPDATE_WHITE_LIST,(copyStatus,rowCopied,rowCopied,srcfiles[6],))
            JMANconnection.commit()
            JMANcursor.execute(UPDATE_FEEDCOUNT,(copyStatus,rowCopied,rowCopied,errMessage,self._InboundCom__jobRunID,srcfiles[4],self._InboundCom__jobRunID,srcfiles[4]))
            JMANconnection.commit()
            DASADMINconnection.close()
            JMANconnection.close()
#
    def processData(self):
        print('Process csv Load')
#         self.collectSourceTargetList()
        print('Execution in progress....')
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            executor.map(self.bubbleProcess,self._InboundCom__fileprocessList)
        # for eachSet in self._InboundCom__fileprocessList:
        #     self.bubbleProcess(eachSet)
    def archiveIncomingFile(self):
        if self.JMAN_RUN_STATUS=='Succeeded':
            for eachIncomingFile in glob.glob(self._InboundCom__sqlload+'/'+self._InboundCom__incomingFileName):
                datePrefix=datetime.now().strftime('%Y%m%d%H%M%S')
                rename(eachIncomingFile,eachIncomingFile.split('.')[0]+datePrefix+'.'+eachIncomingFile.split('.')[1])
                shutil.move(eachIncomingFile.split('.')[0]+datePrefix+'.'+eachIncomingFile.split('.')[1],path.join(self._InboundCom__sqlload,'archive'))
            for eachFile in listdir(self._InboundCom__sqlload):
                if eachFile.endswith(self._InboundCom__incomingFileFormat):
                    remove(path.join(self._InboundCom__sqlload,eachFile))
        else:
            exit(1)
#