# test the connectivity from local machine
#dbutils.library.restartPython()
import logging
import sys
from pyspark.errors import PySparkException
#
if 'TestProject' not in sys.path:
    sys.path.append('./TestProject/')

# Force-clear cached module so the latest file is loaded
#
for mod_name in list(sys.modules):
    if mod_name.startswith('utility'):
        del sys.modules[mod_name]
#
import utility.customLog as CL
# Avoid duplicate handlers on re-run
#logger.handlers = [h for h in logger.handlers if not isinstance(h, CL.CustomHandler)]
logger = logging.getLogger('practiceLog')
logger.setLevel(logging.DEBUG)
customhandler = CL.CustomHandler(spark)
logger.addHandler(customhandler)
#
logger.info('Starting to get row count...')
try:
    count = spark.table('samples.bakehouse.sales_customers').count()
except PySparkException as e:
    logger.error(str(e))
    logger.handlers.clear()
    #dbutils.notebook.exit(e.getMessageParameters())
except Exception as e:
    logger.error(str(e))
    logger.handlers.clear()
    #dbutils.notebook.exit('Exception occurred')
#
logger.info('Fetched row count...')
logger.info(f'rowcount: {count}')
logger.handlers.clear()