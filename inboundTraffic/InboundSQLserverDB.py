'''
Created on Oct 12, 2020

@author:
'''
from inboundTraffic import InboundMaster as IM
from datetime import datetime
import os
import concurrent.futures
import psycopg2.extras
from sqlServerop import DBOperations as DBO
from dbop import DBOperations as ORADBO,DASADMINProfile as OraDASADMINprofile
from postgreop import DBOperations,JMANprofile,DASADMINprofile
from inboundTraffic.SQLstatements import INSERT_WHITE_LIST,INSERT_FEEDCOUNT,SELECT_COL_LIST
from inboundTraffic.SQLstatements import UPDATE_WHITE_LIST,UPDATE_FEEDCOUNT
#
class InboundDB(IM.InboundCom):
    def __init__(self,jobId,DAScolsDict,encoding='latin_1',conversionTable={},escapechar='\\',copyOracle=False):
        self.__DAScolsName=[]
        self.__DAScolsType=[]
        self.__encoding=encoding
        self.__conversionTable=conversionTable
        self.__escapechar=escapechar
        self.__copyOracle=copyOracle
        self.__currTime=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        for key,value in DAScolsDict.items():
            self.__DAScolsName.append(key)
            self.__DAScolsType.append(value)
        super().__init__(jobId)
#
    def getJMANDesc(self,subArea):
        pass
#
    def basicInputCheck(self):
        pass
    def bubbleProcess(self,parms):
        sourceDB,sourceSchema,sourceTable,targetSchema,targetTable,_,whiteListID,_,_,_=parms
#
        try:
            SShandle=DBO.DBOperation(os.path.join(self._InboundCom__CEDL_HOME,'etc',self._InboundCom__remoteDBConfig))
            SSconnection=SShandle.connOpen()
            SScur=SSconnection.cursor()
            SScur.arraysize=1000
        except Exception as e:
            print('Connection to remote server failed:{}'.format(e))
            exit(1)
#
        JMANhandle=DBOperations.DBOperation(JMANprofile)
        JMANconnection=JMANhandle.connOpen()
        JMANcursor=JMANconnection.cursor()
#
        #Insert into WHITE LIST
        JMANcursor.execute(INSERT_WHITE_LIST,(self._InboundCom__jobRunID,whiteListID))
        JMANconnection.commit()
        #Insert into FEEDFILE
        JMANcursor.execute(INSERT_FEEDCOUNT,(self._InboundCom__jobRunID,targetTable,targetSchema,targetTable,))
        JMANconnection.commit()
        #
        DASADMINhandle=DBOperations.DBOperation(DASADMINprofile)
        DASADMINconnection=DASADMINhandle.connOpen()
        DASADMINcur=DASADMINconnection.cursor()
        if self.__copyOracle:
            OraHandle=ORADBO.DBOperation(OraDASADMINprofile)
            oraServiceName=OraHandle.ORADB
            oraUser=OraHandle.ORAUSR
            oraPwdSource=OraHandle.ORAPWD
            dsn=ORADBO.cx_Oracle.makedsn('odsdev.cx6wweeymisp.us-east-1.rds.amazonaws.com','1521',service_name=oraServiceName)
            oraConnect=ORADBO.cx_Oracle.connect(user=oraUser,password=oraPwdSource,dsn=dsn)
            OraCursor=oraConnect.cursor()
            OraCursor.arraysize=1000
#
        print('Processing:{}'.format(parms))
        schemaTable=targetSchema+'.'+targetTable
        try:
            DASADMINcur.execute('TRUNCATE TABLE %s' % schemaTable)
            if self.__copyOracle:
                OraCursor.execute('TRUNCATE TABLE '+targetSchema+'.'+targetTable)
        except DBOperations.DBerror as e:
            print('Error while truncating table {}'.format(schemaTable))
            print(str(e))
            exit(1)
        DASADMINcur.execute(SELECT_COL_LIST,(targetTable.upper(),targetSchema.upper(),tuple(self.__DAScolsName)))
        colIter=[]
        for eachCol in DASADMINcur:
            colIter.append(eachCol[0])
        for eachDASCol in self.__DAScolsName:
            if eachDASCol=='JOB_RUN_ID':
                colIter.append(str(self._InboundCom__jobRunID))
            elif eachDASCol=='SYS_UPD_TS':
                colIter.append("'"+self.__currTime+"'")
#
        selectCol=','.join(colIter)
        selectStatement='SELECT '+selectCol+' FROM '+sourceSchema+'.'+sourceTable
        # print(selectStatement)
        #
        outCol=colIter[:-len(self.__DAScolsName)]
        outCol.extend(self.__DAScolsName)
        SScur.execute(selectStatement)
        timeList=[]
        for eachProperty in SScur.description:
            if eachProperty[1].__name__=='time':
                timeList.append(1)
            else:
                timeList.append(0)
        insertStatement='INSERT INTO '+targetSchema+'.'+targetTable+' ('+','.join(outCol)+\
        ') VALUES ('+'%s,'*len(outCol)
        insertStatement=insertStatement[:-1]+');'
        if self.__copyOracle:
            OraCursor.execute('SELECT COLUMN_NAME FROM ALL_TAB_COLUMNS WHERE OWNER= :b_schema AND TABLE_NAME= :b_table_name ORDER BY COLUMN_ID',b_schema=targetSchema.upper(),b_table_name=targetTable.upper())
            OraColList=[]
            OraColList.extend([eachCol[0] for eachCol in OraCursor])
            insertStmtOracle='INSERT INTO '+targetSchema+'.'+targetTable+' ('+','.join(OraColList)+\
            ') VALUES ('+','.join([':'+str(i+1) for i in range(len(OraColList))])+')'
        # print(insertStatement)
        # print(insertStmtOracle)
        copyStatus='S'
        errMessage=None
        while True:
            try:
                dataList=SScur.fetchmany()
                if dataList:
                    if self.__copyOracle:
                        OraDataList=[]
                        for eachTuple in dataList:
                            interimList=list(eachTuple)
                            interimList[-1]=datetime.strptime(interimList[-1],'%Y-%m-%d %H:%M:%S')
                            for i in range(len(timeList)):
                                if timeList[i]==1:
                                    interimList[i]=str(interimList[i])
                            OraDataList.append(interimList)
                        OraCursor.executemany(insertStmtOracle,OraDataList)
                    psycopg2.extras.execute_batch(DASADMINcur, insertStatement, dataList, 1000)
                else:
                    break
            except Exception as e:
                errf=open(os.path.join(self._InboundCom__CEDL_HOME,'etl','Temp',targetSchema+'_'+targetTable+'.txt'),'w')
                errf.write(str(e))
                errMessage=str(e)
                errf.close()
                copyStatus='F'
        DASADMINcur.execute('SELECT COUNT(*) FROM '+targetSchema+'.'+targetTable)
        rowCopied=DASADMINcur.fetchone()[0]
        DASADMINconnection.commit()
        oraConnect.commit()
        #
        JMANcursor.execute(UPDATE_WHITE_LIST,(copyStatus,rowCopied,rowCopied,whiteListID,))
        JMANconnection.commit()
        JMANcursor.execute(UPDATE_FEEDCOUNT,(copyStatus,rowCopied,rowCopied,errMessage,self._InboundCom__jobRunID,targetTable,self._InboundCom__jobRunID,targetTable))
        JMANconnection.commit()
        # JMANconnection.close()
        # DASADMINconnection.close()
        
    def processData(self):
        print('Process remote DB Load')
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            executor.map(self.bubbleProcess,self._InboundCom__fileprocessList)
        # for eachSet in self._InboundCom__fileprocessList:
        #     self.bubbleProcess(eachSet)
#
    def checkFeedcount(self):
        pass
    # def updJobRunDetails(self):
    #     pass
    def unzipFile(self,location,filename):
        pass