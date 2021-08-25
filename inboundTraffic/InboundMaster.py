'''
Created on Oct 8, 2020

@author: {ANAND.RAJAKRISHNAN2@vnsny.org}
This module has the methods that are common for loading
data from any source object.
'''
from inboundTraffic import InboundInterface as II
import os,io
import glob
from datetime import datetime
from typing import Iterator, Optional
from postgreop import DBOperations,DASADMINprofile,JMANprofile
from inboundTraffic.SQLstatements import JMANJOB,CHECK_FAILED_STATUS
from inboundTraffic.SQLstatements import SELECT_FAILED_TABLE_LIST,SELECT_TABLE_LIST
from inboundTraffic.SQLstatements import SELECT_SUBJECT_AREA,CHECK_RUN_STATUS,UPDATE_JOB_RUN_DETAILS
import shutil
#
class StringIteratorIO(io.TextIOBase):
    def __init__(self, iter: Iterator[str]):
        self._iter = iter
        self._buff = ''
#
    def readable(self) -> bool:
        return True
#
    def _read1(self, n: Optional[int] = 8192) -> str:
        while not self._buff:
            try:
                self._buff = next(self._iter)
            except StopIteration:
                break
        ret = self._buff[:n]
        self._buff = self._buff[len(ret):]
        return ret
#
    def read(self, n: Optional[int] = 8192) -> str:
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
class InboundCom(II.Inbound):
    def __init__(self,jobId):
        self.__jobId=jobId
        self.__unzipFile=False
        #get JMAN handle to connect with the target DB
        try:
            self.__JMANhandle=DBOperations.DBOperation(JMANprofile)
            self.__JMANconnection=self.__JMANhandle.connOpen()
            self.__JMANcursor=self.__JMANconnection.cursor()
        except DBOperations.DBerror as e:
            print('Error connecting with JMAN schema: {}'.format(e))
            exit(1)
        try:
            self.__JMANcursor.execute(JMANJOB,(self.__jobId,))
#             print(self.__JMANcursor.fetchone())
            self.__subjectAreaId,self.__processingFolder,self.__incomingFileLoc,self.__incomingFileName,self.__incomingFileFormat,self.__incomingFileDelim,self.__DASnotifcationFlag,self.__DASnotificationEmailId,self.__DASEmailSubject,self.__businessNotifyFlag,self.__businessNotifyEmailId,self.__businessEmailSubject,self.jobType,self.__schedulerJobName,self.__remoteDBConfig=self.__JMANcursor.fetchone()
        except DBOperations.DBerror as e:
            print('Error fetching data from JMAN.JOB: {}'.format(e))
            exit(1)
        try:
            self.__JMANcursor.execute(SELECT_SUBJECT_AREA,(self.__subjectAreaId,))
            self.__subjectArea,self.__vendorId,self.__supportEmailId,self.__businessEmailId,self.__vendorPhone=self.__JMANcursor.fetchone()
        except DBOperations.DBerror as e:
            print('Error fetching data from JMAN.SUBJECTAREA:{}'.format(e))
            exit(1)
#
        self.__sourceDBTable=self.__jobId+'_table'
        self.__CEDL_HOME=os.environ['CEDL_HOME']
        self.__tempfilesFolder=os.path.join(self.__CEDL_HOME,'tempfiles')
        if self.jobType in ['FULL_REFRESH','CDC','FIXED WIDTH RECON']:
            self.__IPFDIR=os.path.join(self.__CEDL_HOME,'etl/SrcFiles',self.__processingFolder)
            self.__sqlload=os.path.join(self.__IPFDIR,'sqlload')
#         self.__sourceDBTableFile=path.join(self.__tempfilesFolder,self.__sourceDBTable+'.lst')
        self.__currentDay=datetime.today().strftime('%a')
        self.__currDayPattern='%{}%'.format(self.__currentDay)
#
    def checkPrevJobStatus(self):
        try:
            self.__JMANcursor.execute(CHECK_FAILED_STATUS,(self.__jobId,))
            if self.__JMANcursor.rowcount==0:
                self.__jobRunID,self.__runStatus=(0,'Succeeded')
            else:
                self.__jobRunID,self.__runStatus=self.__JMANcursor.fetchone()[0].split(':')
        except DBOperations.DBerror as e:
            print('Error getting previous job status: {}'.format(e))
            exit(1)
        return self.__jobRunID,self.__runStatus
#
    def getFileList(self,fileNameWithWildCard):
#
        if '*' in fileNameWithWildCard:
            fileList=[eachFile for eachFile in glob.glob(os.path.join(self.__sqlload,fileNameWithWildCard))]
        else:
            fileList=[os.path.join(self.__sqlload,fileNameWithWildCard)]
        return fileList
#
    def getFailedTableList(self):
        try:
            self.__JMANcursor.execute(SELECT_FAILED_TABLE_LIST,(self.__jobRunID,))
        except DBOperations.DBerror as e:
            print('Error fetching list of failed tables: {}'.format(e))
            exit(1)
        try:
            self.__fileprocessList=[]
            for eachTuple in self.__JMANcursor:
                #
                #eachTuple[0]: SOURCE_DB
                #eachTuple[1]: SOURCE_SCHEMA
                #eachTuple[2]: list of SOURCE_TABLE_NAME + self.__incomingFileFormat
                #eachTuple[3]: TARGET_SCHEMA
                #eachTuple[4]: TARGET_TABLE_NAME
                #eachTuple[5]: PK_COLUMN
                #eachTuple[6]: TABLE_REFRESH_WHITE_LIST_ID
                #eachTuple[7]: DB_LINK
                #eachTuple[8]: COPY_STATEMENT
                #eachTuple[9]: TARGET_TABLE_STG_NAME
                #
                if self.jobType in ['FULL_REFRESH','CDC','FIXED WIDTH RECON']:
                    self.__fileprocessList.append((eachTuple[0],eachTuple[1],self.getFileList(eachTuple[2]+self.__incomingFileFormat),eachTuple[3],eachTuple[4],eachTuple[5],eachTuple[6],eachTuple[7],eachTuple[8],eachTuple[9]))
                elif self.jobType in ['DB_FULL_REFRESH']:
                    self.__fileprocessList.append((eachTuple[0],eachTuple[1],eachTuple[2],eachTuple[3],eachTuple[4],eachTuple[5],eachTuple[6],eachTuple[7],eachTuple[8],eachTuple[9]))
        except Exception as e:
            print('Error building the failed source file list: {}'.format(e))
            exit(1)
#
    def getTableList(self):
        try:
            self.__JMANcursor.execute(SELECT_TABLE_LIST,(self.__jobId,
                                                         self.__currDayPattern,))
        except DBOperations.DBerror as e:
            print('Error fetching list of tables from JMAN TABLE_REFRESH_WHITE_LIST: {}'.format(e))
            exit(1)
        try:
            self.__fileprocessList=[]
            for eachTuple in self.__JMANcursor:
                #
                #eachTuple[0]: SOURCE_DB
                #eachTuple[1]: SOURCE_SCHEMA
                #eachTuple[2]: SOURCE_TABLE_NAME + self.__incomingFileFormat
                #eachTuple[3]: TARGET_SCHEMA
                #eachTuple[4]: TARGET_TABLE_NAME
                #eachTuple[5]: PK_COLUMN
                #eachTuple[6]: TABLE_REFRESH_WHITE_LIST_ID
                #eachTuple[7]: DB_LINK
                #eachTuple[8]: COPY_STATEMENT
                #eachTuple[9]: TARGET_TABLE_STG_NAME
                #
                if self.jobType in ['FULL_REFRESH','CDC','FIXED WIDTH RECON']:
                    self.__fileprocessList.append((eachTuple[0],eachTuple[1],self.getFileList(eachTuple[2]+('' if self.__incomingFileFormat is None else self.__incomingFileFormat)),eachTuple[3],eachTuple[4],eachTuple[5],eachTuple[6],eachTuple[7],eachTuple[8],eachTuple[9]))
                elif self.jobType in ['DB_FULL_REFRESH']:
                    self.__fileprocessList.append((eachTuple[0],eachTuple[1],eachTuple[2],eachTuple[3],eachTuple[4],eachTuple[5],eachTuple[6],eachTuple[7],eachTuple[8],eachTuple[9]))
        except Exception as e:
            print('Error building the source file list: {}'.format(e))
            exit(1)
        pass
#
    def unzipIncoming(self,zipAlgorithm='zip'):
        self.__zipFileName=''
        for eachIncomingFile in glob.glob(self.__incomingFileLoc+self.__incomingFileName):
            shutil.move(eachIncomingFile,self.__sqlload)
        for eachZipFile in glob.glob(self.__sqlload+'/'+self.__incomingFileName):
            self.__zipFileName+=eachZipFile.split('/')[-1]
            if zipAlgorithm=='zip':
                import zipfile
                with zipfile.ZipFile(eachZipFile,'r') as objZipFile:
                    objZipFile.extractall(self.__sqlload)
            elif zipAlgorithm=='tar':
                import tarfile
                objTar=tarfile.open(eachZipFile)
                objTar.extractall(self.__sqlload)
                objTar.close()
        self.__unzipFile=True
#
    def getJobRunId(self):
        try:
            if self.__unzipFile:
                pass
            else:
                self.__zipFileName='NA'
            print(self.__jobId,self.__schedulerJobName,self.__zipFileName)
            self.__JMANcursor.execute("SELECT jman.insjobrundetails(%s, %s, %s, %s, %s, %s, %s)",(self.__jobId,self.__schedulerJobName,self.__zipFileName,0,0,'N','N'))
            self.__jobRunID=self.__JMANcursor.fetchone()[0]
            self.__JMANconnection.commit()
            print('JOB_RUN_ID:{}'.format(self.__jobRunID))
        except DBOperations.DBerror as e:
            print('Error executing JMAN.INSJOBRUNDETAILS:{}'.format(e))
            exit(1)
#
    def processData(self):
        pass
    def checkFeedcount(self):
        pass
    def updJobRunDetails(self):
        self.__JMANcursor.execute(CHECK_RUN_STATUS,(self.__jobRunID,self.__jobRunID,))
        self.JMAN_RUN_STATUS='Succeeded' if self.__JMANcursor.fetchone()[0].split('-')[1]=='0' else 'Failed'
        print('JMAN RUN STATUS:{}'.format(self.JMAN_RUN_STATUS))
#         if self.JMAN_RUN_STATUS=='Succeeded':
            # Move zip files to archive folder
#             for eachIncomingFile in glob.glob(self.__sqlload+'/'+self.__incomingFileName):
#                 shutil.move(eachIncomingFile,os.path.join(self.__sqlload,'archive'))
            # Delete all unzipped files
#             for eachFile in os.listdir(self.__sqlload):
#                 if eachFile.endswith(self.__incomingFileFormat):
#                     os.remove(os.path.join(self.__sqlload,eachFile))
        self.__JMANcursor.execute(UPDATE_JOB_RUN_DETAILS,(self.JMAN_RUN_STATUS,self.__jobRunID,self.__jobRunID,))
        self.__JMANconnection.commit()
#        self.__JMANhandle.connClose()