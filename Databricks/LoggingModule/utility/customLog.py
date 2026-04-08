import logging
from pyspark.sql.types import StructType, StructField, StringType,TimestampType,IntegerType,LongType
from pyspark.dbutils import DBUtils
from datetime import datetime
from zoneinfo import ZoneInfo
import json
#
class CustomHandler(logging.Handler):
    def __init__(self, sparkContext):
        super().__init__()
        self.schema = StructType([
            StructField("timeOfMessage", TimestampType(), True),
            StructField("level", StringType(), True),
            StructField("handlerName", StringType(), True),
            StructField("lineNumber", IntegerType(), True),
            StructField("notebookPath", StringType(), True),
            StructField("notebookId", LongType(), True),
            StructField("message", StringType(), True)
        ])
        self.timeZoneToronto = ZoneInfo("America/Toronto")
        self.dbutils = DBUtils(sparkContext)
        self.sparkContext = sparkContext
#
    def emit(self,record):
        if record:
            job_params = self.dbutils.notebook.entry_point.getDbutils().notebook().getContext().safeToJson()
            params = json.loads(job_params)
            #currentRunId = params["attributes"]["currentRunId"]
            notebookPath = params['attributes']['notebook_path']
            notebookId = params['attributes']["notebook_id"]
            #logMessage = f"{datetime.now(self.timeZoneToronto)}~{record.levelname}~{record.name}~linenumber:{record.lineno}~notebook path:{notebookPath}~notebookId: {notebookId}~{record.msg}"
            #print(f"{datetime.now(self.timeZoneToronto)}~{record.levelname}~{record.name}~linenumber:{record.lineno}~notebook path:{notebookPath}~notebookId: {notebookId}~{record.msg}")
            logData = list()
            logData.append((datetime.now(self.timeZoneToronto),record.levelname,record.name,record.lineno,notebookPath,int(notebookId),record.msg))
            logDataDF = self.sparkContext.createDataFrame(logData, schema=self.schema)
            logDataDF.write.mode('append').saveAsTable('workspace.default.log')
#
if __name__ == '__main__':
    customhandler = CustomHandler(spark)
    logger = logging.getLogger('practiceLog')
    logger.addHandler(customhandler)
    logger.setLevel(logging.DEBUG)
    try:
        _ = 1/0
    except Exception as e:
        logger.error(str(e))
        exit(1)
#