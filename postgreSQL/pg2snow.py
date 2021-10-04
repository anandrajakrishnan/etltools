import boto3
import io
import datetime
from typing import Iterator, Optional
from postgreop import DBOperations as DBO,DASADMINprofile
import snowflake.connector as sc
#
copyList=[('CMGC','ADV_DIR_INDICATORS','CMGC','ADV_DIR_INDICATORS'),
('CMGC','APPOINTMENT','CMGC','APPOINTMENT'),
('CMGC','BENEFIT_PROGRAM','CMGC','BENEFIT_PROGRAM'),
('CMGC','CM_MA_SERVICPLAN_SCRPTFORM_STS','CMGC','CM_MA_SERVICPLAN_SCRPTFORM_STS'),
('CMGC','HEALTH_INDICATOR_PARAMETER','CMGC','HEALTH_INDICATOR_PARAMETER'),
('CMGC','HEALTH_INDICATOR_RECORD','CMGC','HEALTH_INDICATOR_RECORD'),
('CMGC','HEALTH_NOTE_TYPE','CMGC','HEALTH_NOTE_TYPE'),
('CMGC','HEALTH_NOTES','CMGC','HEALTH_NOTES'),
('CMGC','INTERNAL_PROGRAM_REASON','CMGC','INTERNAL_PROGRAM_REASON'),
('CMGC','LETTER_QUEUE','CMGC','LETTER_QUEUE'),
('CMGC','LETTER_TEMPLATE','CMGC','LETTER_TEMPLATE'),
('CMGC','MEM_BENF_PLAN','CMGC','MEM_BENF_PLAN'),
('CMGC','MEM_BENF_PROG','CMGC','MEM_BENF_PROG'),
('CMGC','MEMBER_ASSESSMENT_TYPE','CMGC','MEMBER_ASSESSMENT_TYPE'),
('CMGC','MEMBER_CARESTAFF','CMGC','MEMBER_CARESTAFF'),
('CMGC','MEMBER_SERVICE_INTERRUPTION','CMGC','MEMBER_SERVICE_INTERRUPTION'),
('CMGC','PAT_ADV_DIR_INDICATORS','CMGC','PAT_ADV_DIR_INDICATORS'),
('CMGC','PATIENT_INDEX','CMGC','PATIENT_INDEX'),
('CMGC','PATIENT_PHYSICIAN','CMGC','PATIENT_PHYSICIAN'),
('CMGC','PATIENT_PRIMARY_CAREGIVER','CMGC','PATIENT_PRIMARY_CAREGIVER'),
('CMGC','PATIENT_REFERRAL_TYPE','CMGC','PATIENT_REFERRAL_TYPE'),
('CMGC','PROVIDER_INDEX','CMGC','PROVIDER_INDEX'),
('CMGC','SCPT_ADMIN_QUESTION','CMGC','SCPT_ADMIN_QUESTION'),
('CMGC','SCPT_ADMIN_QUESTION_OPTION','CMGC','SCPT_ADMIN_QUESTION_OPTION'),
('CMGC','SCPT_FORM_PAT_REVIEW_STATUS','CMGC','SCPT_FORM_PAT_REVIEW_STATUS'),
('CMGC','SCPT_FORM_PATIENT_INFO','CMGC','SCPT_FORM_PATIENT_INFO'),
('CMGC','SCPT_PAT_SCRIPT_RUN_LOG_DET','CMGC','SCPT_PAT_SCRIPT_RUN_LOG_DET'),
('CMGC','SCPT_QUESTION_RESPONSE','CMGC','SCPT_QUESTION_RESPONSE'),
('CMGC','SCPT_SCRIPT_RUN_STATUS','CMGC','SCPT_SCRIPT_RUN_STATUS'),
('CMGC','SERVICE_INTERRUPTION','CMGC','SERVICE_INTERRUPTION'),
('CMGC','UM_278_LOG','CMGC','UM_278_LOG'),
('CMGC','SCPT_ADMIN_QUESTION_SUBOPTION','CMGC','SCPT_ADMIN_QUESTION_SUBOPTION'),
('CMGC','CMN_MA_BUSINESS_HIERARCHY_PROGRAM','CMGC','CMN_MA_BUSINESS_HIERARCHY_PROGRAM'),
('CMGC','PATIENT_HEALTH_NOTES','CMGC','PATIENT_HEALTH_NOTES'),
('CMGC','PROVIDER_NETWORK_STATUS','CMGC','PROVIDER_NETWORK_STATUS'),
]
class BufferIteratorIO(io.BufferedIOBase):
    def __init__(self, iter: Iterator[str]):
        self._iter = iter
        self._buff = ''
#
    def readable(self) -> bool:
        return True
#
    def _read1(self, n: Optional[int] = 8192) -> bytes:
        while not self._buff:
            try:
                self._buff = next(self._iter)
            except StopIteration:
                break
        ret = self._buff[:n]
        self._buff = self._buff[len(ret):]
        return ret
#
    def read(self, n: Optional[int] = None) -> bytes:
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
        return bytes(''.join(line),'utf-8')
#
def buildcsvData(schemaName,TableName):
    # postgreSQL connection
    DASADMINhandle=DBO.DBOperation(DASADMINprofile)
    DASADMINconnection=DASADMINhandle.connOpen()
    DASADMINcur=DASADMINconnection.cursor()
    inSQL='select * from '+schemaName+'.'+TableName+' limit 1000000'
    DASADMINcur.execute(inSQL)
    numCols=len(DASADMINcur.description)
    quote='"'
    for eachRow in DASADMINcur:
        rowList=list(eachRow)
        for i in range(numCols):
            extraSpecialChar=specialCharacter='N'
            if isinstance(rowList[i],str):
                if '"' in rowList[i] or '\\' in rowList[i]:
                    rowList[i]=rowList[i].replace('\\','\\\\').replace('"','\\"')
                    extraSpecialChar='Y'
                if '\r' in rowList[i] or '\n' in rowList[i] or chr(31) in rowList[i]:
                    rowList[i]=quote+rowList[i]+quote
                    specialCharacter='Y'
                if extraSpecialChar=='Y' and specialCharacter=='N':
                    rowList[i]=quote+rowList[i]+quote
            elif isinstance(rowList[i],datetime.datetime):
                rowList[i]=rowList[i].strftime('%Y-%m-%d %H:%M:%S.%f')[:-3] if rowList[i] is not None else ''
            elif rowList[i] is None:
                rowList[i]=''
            else:
                rowList[i]=str(rowList[i])
        yield chr(31).join(rowList)+'\n'
        # print(chr(31).join(rowList))
#
# aws connection
s3=boto3.client('s3',
                aws_access_key_id='xxxxxxxxxxxxxxxxxxx',
                aws_secret_access_key='xxxxxxxxxxxxxxxxxxxxxxx')
dataIterator=BufferIteratorIO((buildcsvData('dw_owner','tmg_claims_diagnosis')))
print(datetime.datetime.now())
try:
    s3.upload_fileobj(dataIterator,'vnsny-das-staging-test','tmg_claims_diagnosis.csv')
except Exception as e:
    print(str(e))
print(datetime.datetime.now())
ctx=sc.connect(user='xxxxx',
               password='xxxxxxx',
               account='xxxxxxxxx.us-east-1.privatelink')
snowCursor=ctx.cursor()
copySQL="""
COPY INTO CHOICE.TMG_CLAIMS_DIAGNOSIS
FROM s3://vnsny-das-staging-test/tmg_claims_diagnosis.csv
CREDENTIALS = (aws_key_id='xxxxxxxxxxxxxxxxxxxx' aws_secret_key='xxxxxxxxxxxxxxxxxxxxxxxxxxxx')
FILE_FORMAT = (TYPE=CSV FIELD_DELIMITER= '0x1f' TIMESTAMP_FORMAT='YYYY-MM-DD HH24:MI:SS.FF3' DATE_FORMAT='YYYY-MM-DD HH24:MI:SS' NULL_IF=())
"""
snowCursor.execute(copySQL)
print(datetime.datetime.now())
# dataIterator=StringIteratorIO((buildcsvData('cmgc','appointment')))
# for _ in range(5):
