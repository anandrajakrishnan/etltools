'''
Created on Oct 14, 2020

@author: ANAND_RA_Temp
'''
JMANJOB="""
select
    subject_area_id,
    processing_folder_name,
    dependency_file_location,
    dependency_file_name,
    dependency_file_format,
    dependency_file_delimiter,
    das_notification_flag,
    das_notification_email_id,
    das_notification_email_subject,
    business_notification_flag,
    business_notification_email_id,
    business_notification_email_subject,
    job_type,
    controlm_job_name,
    remote_db_config
from
    jman.job
where
    is_active = 'Y'
    and job_id =%s
"""
SELECT_SUBJECT_AREA="""
SELECT subject_area_name,
       vendor_id,
       vendor_support_email_id,
       vendor_business_email_id,
       vendor_phone_no
  FROM jman.subjectarea
 WHERE subject_area_id = %s
"""
SELECT_VENDOR_DESC="""
SELECT VENDOR,
       FILE_FORMAT,
       NUM_ATTR,
       DELIMITER_TYPE,
       INF_WF_NAME,
       INF_SES_NAME,
       CONTROLM_JOB_NAME,
       JOB_ID,
       IS_EXT,
       TIER,
       SEGMENTS,
       VENDOR_ID
  FROM JMAN.VENDOR_DESC
 WHERE SUBJECT_AREA = %s
 """
CHECK_FAILED_STATUS="""
SELECT JOB_RUN_ID || ':' || COALESCE (RUN_STATUS, 'Failed')
  FROM JMAN.JOBRUNDETAILS
 WHERE JOB_RUN_ID = (SELECT MAX (JOB_RUN_ID)
                       FROM JMAN.JOBRUNDETAILS
                      WHERE JOB_ID = %s )
"""
SELECT_FAILED_TABLE_LIST="""
SELECT    SOURCE_DB
          ,SOURCE_SCHEMA
          ,SOURCE_TABLE_NAME
          ,TARGET_SCHEMA
          ,TARGET_TABLE_NAME
          ,PK_COLUMN
          ,TABLE_REFRESH_WHITE_LIST_ID
          ,DB_LINK
          ,COPY_STATEMENT
          ,TARGET_TABLE_STG_NAME
    FROM JMAN.TABLE_REFRESH_WHITE_LIST
   WHERE JMAN_TGT_JOB_RUN_ID = %s AND STATUS != 'S'
ORDER BY TABLE_REFRESH_WHITE_LIST_ID
"""
SELECT_TABLE_LIST="""
SELECT    SOURCE_DB
          ,SOURCE_SCHEMA
          ,SOURCE_TABLE_NAME
          ,TARGET_SCHEMA
          ,TARGET_TABLE_NAME
          ,PK_COLUMN
          ,TABLE_REFRESH_WHITE_LIST_ID
          ,DB_LINK
          ,COPY_STATEMENT
          ,TARGET_TABLE_STG_NAME
    FROM JMAN.TABLE_REFRESH_WHITE_LIST
   WHERE     IS_ACTIVE = 'Y'
         AND JOB_ID=%s
         AND (UPPER (SCHEDULE) LIKE UPPER (%s) OR SCHEDULE = 'Adhoc')
ORDER BY TABLE_REFRESH_WHITE_LIST_ID
"""
#
SELECT_FW_TABLE_LIST="""
SELECT    SOURCE_TABLE_NAME
          ,TARGET_SCHEMA
          ,TARGET_TABLE_NAME
          ,FW_COLUMN_WIDTH
    FROM JMAN.TABLE_REFRESH_WHITE_LIST
   WHERE     IS_ACTIVE = 'Y'
         AND JOB_ID=%s
         AND (UPPER (SCHEDULE) LIKE UPPER (%s) OR SCHEDULE = 'Adhoc')
ORDER BY TABLE_REFRESH_WHITE_LIST_ID
"""
#
SELECT_COL_LIST="""
select
    column_name
from
    information_schema.columns
where
    upper(table_name) = %s
    and upper(table_schema)=%s
    and upper(column_name)not in %s
order by
    ordinal_position
"""
#
INSERT_WHITE_LIST="""
update
    JMAN.TABLE_REFRESH_WHITE_LIST
set
    STATUS = 'P',
    JMAN_TGT_JOB_RUN_ID = %s,
    LAST_START_TS = current_timestamp
where
    TABLE_REFRESH_WHITE_LIST_ID = %s
"""
#
INSERT_FEEDCOUNT="""
insert
    into
    JMAN.FEEDCOUNT (JOB_RUN_ID,
    TABLE_NAME,
    SOURCE_SUCCESS_ROWS,
    SOURCE_FAILED_ROWS,
    TARGET_SUCCESS_ROWS,
    TARGET_FAILED_ROWS,
    STATUS,
    SESSION_NAME,
    INSTANCE_NAME,
    START_TIME)
values (%s,
%s,
0,
0,
0,
0,
'P',
%s || '.' || %s,
'SQL_LOAD_REFRESH',
current_timestamp)
"""
#
TRUNCATE_TABLE="""
TRUNCATE TABLE %s
"""
#
UPDATE_WHITE_LIST="""
update
    JMAN.TABLE_REFRESH_WHITE_LIST
set
    STATUS = %s,
    SRC_COUNT = %s,
    TGT_COUNT = %s,
    LAST_END_TS = current_timestamp
where
    TABLE_REFRESH_WHITE_LIST_ID = %s
"""
#
UPDATE_FEEDCOUNT="""
update
    JMAN.FEEDCOUNT
set
    STATUS = %s,
    SOURCE_SUCCESS_ROWS = %s,
    TARGET_SUCCESS_ROWS = %s,
    END_TIME = current_timestamp,
    ERROR_MSG = %s
where
    JOB_RUN_ID = %s
    and TABLE_NAME = %s
    and START_TIME = (
    select
        MAX(START_TIME)
    from
        JMAN.FEEDCOUNT
    where
        JOB_RUN_ID = %s
        and TABLE_NAME = %s)
"""
#
CHECK_RUN_STATUS="""
select
    'count_start-' || count(*)
from
    JMAN.FEEDCOUNT
where
    STATUS = 'F'
    and JOB_RUN_ID = %s
    and (TABLE_NAME,
    SESSION_NAME) not in (
    select
        TABLE_NAME,
        SESSION_NAME
    from
    JMAN.FEEDCOUNT
    where
        STATUS = 'S'
        and JOB_RUN_ID = %s )
"""
#
UPDATE_JOB_RUN_DETAILS="""
update
    JMAN.JOBRUNDETAILS
set
    END_TS = current_timestamp,
    RUN_STATUS = %s,
    ROWS_PROCESSED = (
    select
        sum(TARGET_SUCCESS_ROWS)
    from
        FEEDCOUNT
    where
        JOB_RUN_ID = %s
        and STATUS = 'S')
where
    JOB_RUN_ID = %s
"""
#
GET_COLUMN_DATATYPE="""
select
    A.COLUMN_NAME,
    UPPER(A.UDT_NAME),
    A.ORDINAL_POSITION
from
    INFORMATION_SCHEMA.columns A
where
    UPPER(A.TABLE_SCHEMA)= %s
    and UPPER(A.TABLE_NAME)= %s
    and UPPER(A.COLUMN_NAME) not in %s
    and A.COLUMN_NAME not in (
    select
        C.COLUMN_NAME
    from
        PG_CATALOG.PG_STATIO_ALL_TABLES as ST
    inner join PG_CATALOG.PG_DESCRIPTION PGD on
        (PGD.OBJOID = ST.RELID)
    inner join INFORMATION_SCHEMA.COLUMNS C on
        (PGD.OBJSUBID = C.ORDINAL_POSITION
        and C.TABLE_SCHEMA = ST.SCHEMANAME
        and C.TABLE_NAME = ST.RELNAME)
    where
        UPPER(C.TABLE_SCHEMA)= %s
        and UPPER(C.TABLE_NAME)= %s
        and PGD.DESCRIPTION = 'SURROGATE KEY')
order by
    A.ORDINAL_POSITION
"""
#
GET_COLUMN_SK_COUNT="""
select
    A.COLUMN_NAME
from
    INFORMATION_SCHEMA.COLUMNS A
where
    UPPER(A.TABLE_SCHEMA)= %s
    and UPPER(A.TABLE_NAME)= %s
    and A.COLUMN_NAME in (
    select
        C.COLUMN_NAME
    from
        PG_CATALOG.PG_STATIO_ALL_TABLES as ST
    inner join PG_CATALOG.PG_DESCRIPTION PGD on
        (PGD.OBJOID = ST.RELID)
    inner join INFORMATION_SCHEMA.COLUMNS C on
        (PGD.OBJSUBID = C.ORDINAL_POSITION
        and C.TABLE_SCHEMA = ST.SCHEMANAME
        and C.TABLE_NAME = ST.RELNAME)
    where
        UPPER(C.TABLE_SCHEMA)= %s
        and UPPER(C.TABLE_NAME)= %s
        and PGD.DESCRIPTION = 'SURROGATE KEY')
"""
#