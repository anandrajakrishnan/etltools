'''
Created on Apr 8, 2021

@author: ANAND_RA_Temp
'''
from inboundTraffic import InboundMaster as IM
from os import path,listdir,remove,rename
import io
import glob,shutil
import csv
from datetime import datetime
from typing import Iterator, Optional
import concurrent.futures
from postgreop import DBOperations,JMANprofile,DASBATCHRWprofile
from inboundTraffic.SQLstatements import SELECT_COL_LIST,INSERT_WHITE_LIST,INSERT_FEEDCOUNT
from inboundTraffic.SQLstatements import UPDATE_WHITE_LIST,UPDATE_FEEDCOUNT
#
class StringIteratorIO(io.TextIOBase):
    def __init__(self, iter: Iterator[str]):
        self._iter = iter
        self._buff = ''
#
    def readable(self) -> bool:
        return True
#
    def _read1(self, n: Optional[int] = None) -> str:
        while not self._buff:
            try:
                self._buff = next(self._iter)
            except StopIteration:
                break
        ret = self._buff[:n]
        self._buff = self._buff[len(ret):]
        return ret
#
    def read(self, n: Optional[int] = None) -> str:
        line = []
        if n is None or n < 0:
            while True:
                m = self._read1()
                if not m:
                    break
                line.append(m)
        else:
            while n > 0:
                m = self._read1(n)
                if not m:
                    break
                n -= len(m)
                line.append(m)
        return ''.join(line)
#
class InboundCSV(IM.InboundCom):
    def __init__(self,jobId,DAScolsDict,headerRows,encoding='latin_1',conversionTable={},fileDelimiter=',',lineSep='\r\n',escapechar=None,addTStoArchive='N'):
        self.__DAScolsName=[]
        self.__DAScolsType=[]
        self.__headerRows=headerRows
        self.__encoding=encoding
        self.__conversionTable=conversionTable
        self.__fileDelimiter=fileDelimiter
        self.__lineSep=lineSep
        self.__escapechar=escapechar
        self.__addTStoArchive=addTStoArchive
        self.__currTime=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        super().__init__(jobId)
#         self.__tailData=''
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
    def ETLtransform(self,fileObj):
#
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
            yield(chr(31).join(eachLine).translate(self.__conversionTable)+DASdata+'\n')
#
    def ETLtransformCopy(self,fileObj):
#
#        csvIter=csv.reader((line.replace('\0','') for line in fileObj),delimiter=self.__fileDelimiter,quoting=csv.QUOTE_ALL,quotechar='"',escapechar=self.__escapechar)
        DASdata=''
        for eachValue in self.__DAScolsType:
            if eachValue=='jobRunId':
                DASdata+=self.__fileDelimiter+'"'+str(self._InboundCom__jobRunID)+'"'
            elif eachValue=='timestamp':
                DASdata+=self.__fileDelimiter+'"'+self.__currTime+'"'
        for _ in range(self.__headerRows):
            next(fileObj)
        for eachLine in fileObj:
            yield(self.__fileDelimiter+eachLine[:-len(self.__lineSep)]+DASdata+'\n')
#
    def bubbleProcess(self,srcfiles):
#         inFile = srcfiles[2]
#         schema_name = srcfiles[3]
#         table_name=srcfiles[4]
        #Get JMAN cursor
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
        DASBATCHRWhandle=DBOperations.DBOperation(DASBATCHRWprofile)
        DASBATCHRWconnection=DASBATCHRWhandle.connOpen()
        DASBATCHRWcur=DASBATCHRWconnection.cursor()
        print('Processing:{}'.format(srcfiles))
        rowCopied=0
        if srcfiles[8] is None:
#
            try:
                schemaTable=srcfiles[3]+'.'+srcfiles[9]
                DASBATCHRWcur.execute('TRUNCATE TABLE %s' % schemaTable)
            except DBOperations.DBerror as e:
                print('Error while truncating table {}'.format(schemaTable))
                print(e)
                exit(1)
            for eachFile in srcfiles[2]:
                f=open(eachFile,'r',encoding=self.__encoding,newline=self.__lineSep)
                objColList=self.getColumnIter(srcfiles[3],srcfiles[4],DASBATCHRWcur)
#             dataIterator=StringIteratorIO((self.ETLtransform(f)))
                dataIterator=StringIteratorIO((self.ETLtransform(f)))
                try:
                    DASBATCHRWcur.copy_from(dataIterator,schemaTable,sep=chr(31),size=8192,null='',columns=objColList)
                    rowCopied+=DASBATCHRWcur.rowcount
                except Exception as e:
                    errf=open(path.join(self._InboundCom__CEDL_HOME,'etl','Temp',srcfiles[3]+'_'+srcfiles[4]+'.txt'),'w')
                    errf.write('File that caused error:{}'.format(eachFile))
                    errf.write(str(e))
                    errf.close()
                    print(e)
                    f.close()
                    exit(1)
            try:
                # DASBATCHRWcur.copy_from(dataIterator,schemaTable,sep=chr(31),size=8192,null='',columns=objColList)
                # rowCopied=DASBATCHRWcur.rowcount
#               Delete the incoming rows from target table
                equateString=''
                for eachPK in srcfiles[5].split(','):
                    if len(equateString)==0:
                        equateString='T.'+eachPK+'=S.'+eachPK
                    else:
                        equateString+=' AND T.'+eachPK+'=S.'+eachPK
                DelStatement='DELETE FROM '+srcfiles[3]+'.'+srcfiles[4]+' T WHERE EXISTS(SELECT 1 FROM '+srcfiles[3]+'.'+srcfiles[9]+' S WHERE '+equateString+')'
                DASBATCHRWcur.execute(DelStatement)
                DASBATCHRWconnection.commit()
#               Insert the incoming rows from staging table
                InsertStatement='INSERT INTO '+srcfiles[3]+'.'+srcfiles[4]+' ('+','.join(objColList)+') SELECT '+','.join(objColList)+' FROM '+srcfiles[3]+'.'+srcfiles[9]
                DASBATCHRWcur.execute(InsertStatement)
                DASBATCHRWconnection.commit()
                copyStatus='S'
                JMANcursor.execute(UPDATE_WHITE_LIST,(copyStatus,srcfiles[6],))
                JMANconnection.commit()
                JMANcursor.execute(UPDATE_FEEDCOUNT,(copyStatus,rowCopied,rowCopied,None,self._InboundCom__jobRunID,srcfiles[4],self._InboundCom__jobRunID,srcfiles[4]))
                JMANconnection.commit()
            except Exception as e:
                errf=open(path.join(self._InboundCom__CEDL_HOME,'etl','Temp',srcfiles[3]+'_'+srcfiles[4]+'.txt'),'w')
                errf.write(str(e))
                errf.close()
                print(e)
                f.close()
                copyStatus='F'
                JMANcursor.execute(UPDATE_WHITE_LIST,(copyStatus,srcfiles[6],))
                JMANconnection.commit()
                JMANcursor.execute(UPDATE_FEEDCOUNT,(copyStatus,0,0,str(e)[0:5000],self._InboundCom__jobRunID,srcfiles[4],self._InboundCom__jobRunID,srcfiles[4]))
                JMANconnection.commit()
                exit(1)
            dataIterator=None
            f.close()
            DASBATCHRWconnection.commit()
            DASBATCHRWconnection.close()
        else:
            try:
                schemaTable=srcfiles[3]+'.'+srcfiles[9]
                DASBATCHRWcur.execute('TRUNCATE TABLE %s' % schemaTable)
            except DBOperations.DBerror as e:
                print('Error while truncating table {}'.format(schemaTable))
                print(e)
                exit(1)
            for eachFile in srcfiles[2]:
                f=open(eachFile,'r',encoding=self.__encoding,newline=self.__lineSep)
                dataIterator=StringIteratorIO((self.ETLtransformCopy(f)))
                try:
    #                 print(dataIterator.read())
                    DASBATCHRWcur.copy_expert(srcfiles[8],dataIterator)
                    rowCopied+=DASBATCHRWcur.rowcount
                    # copyStatus='S'
                    # JMANcursor.execute(UPDATE_WHITE_LIST,(copyStatus,srcfiles[6],))
                    # JMANconnection.commit()
                    # JMANcursor.execute(UPDATE_FEEDCOUNT,(copyStatus,rowCopied,rowCopied,None,self._InboundCom__jobRunID,srcfiles[4],self._InboundCom__jobRunID,srcfiles[4]))
                    # JMANconnection.commit()
                except Exception as e:
                    errf=open(path.join(self._InboundCom__CEDL_HOME,'etl','Temp',srcfiles[3]+'_'+srcfiles[4]+'.txt'),'w')
                    errf.write(str(e))
                    errf.close()
                    print(e)
                    f.close()
                    copyStatus='F'
                    JMANcursor.execute(UPDATE_WHITE_LIST,(copyStatus,srcfiles[6],))
                    JMANconnection.commit()
                    JMANcursor.execute(UPDATE_FEEDCOUNT,(copyStatus,0,0,str(e)[0:5000],self._InboundCom__jobRunID,srcfiles[4],self._InboundCom__jobRunID,srcfiles[4]))
                    JMANconnection.commit()
                    exit(1)
                dataIterator=None
                f.close()
                DASBATCHRWconnection.commit()
            copyStatus='S'
            JMANcursor.execute(UPDATE_WHITE_LIST,(copyStatus,srcfiles[6],))
            JMANconnection.commit()
            JMANcursor.execute(UPDATE_FEEDCOUNT,(copyStatus,rowCopied,rowCopied,None,self._InboundCom__jobRunID,srcfiles[4],self._InboundCom__jobRunID,srcfiles[4]))
            JMANconnection.commit()
            DASBATCHRWconnection.close()
#
    def processData(self):
#
        print('Execution in progress....')
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            executor.map(self.bubbleProcess,self._InboundCom__fileprocessList)
#         for eachSet in self._InboundCom__fileprocessList:
#             self.bubbleProcess(eachSet)
    def archiveIncomingFile(self):
        if self.JMAN_RUN_STATUS=='Succeeded':
            for eachIncomingFile in glob.glob(self._InboundCom__sqlload+'/'+self._InboundCom__incomingFileName):
                datePrefix=datetime.now().strftime('%Y%m%d%H%M%S')
                rename(eachIncomingFile,eachIncomingFile.split('.')[0]+datePrefix+'.'+eachIncomingFile.split('.')[1])
                shutil.move(eachIncomingFile.split('.')[0]+datePrefix+'.'+eachIncomingFile.split('.')[1],path.join(self._InboundCom__sqlload,'archive'))
            for eachFile in listdir(self._InboundCom__sqlload):
                if eachFile.endswith(self._InboundCom__incomingFileFormat):
                    remove(path.join(self._InboundCom__sqlload,eachFile))
#