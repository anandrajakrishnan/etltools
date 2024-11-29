--Get DDL with grants
SET (TYPE_,DB_,SCHEMA_,OBJECT_)=('TABLE','DB_NAME','SCHEMA_NAME','OBJECT_NAME')
;

SELECT LISTAGG(DDL_STMT,'\n') WITHIN GROUP (ORDER BY SEQ_) FROM
(
SELECT GET_DDL($TYPE_,$DB_ || '.' || $SCHEMA_ || '.' || $OBJECT_,true) DDL_STMT, 1 AS SEQ_
UNION
SELECT 'GRANT ' || A.PRIVILEGE_TYPE || ' ON ' || A.OBJECT_TYPE || ' ' ||
       CASE WHEN A.OBJECT_CATALOG IS NULL THEN '' ELSE A.OBJECT_CATALOG || '.' END ||
       CASE WHEN A.OBJECT_SCHEMA IS NULL THEN '' ELSE A.OBJECT_SCHEMA || '.' END || A.OBJECT_NAME ||
       ' TO ' || CASE WHEN UPPER(GRANTEE) LIKE '%_SHARE' THEN 'SHARE' ELSE 'ROLE' END ||
       ' ' || A.GRANTEE || ';' GRANT_STATEMENTS, 2 AS SEQ_
FROM DB_NAME.INFORMATION_SCHEMA.OBJECT_PRIVILEGES A
WHERE A.OBJECT_SCHEMA = $SCHEMA_
AND A.OBJECT_NAME =$OBJECT_
AND OBJECT_CATALOG=$DB_
AND GRANTOR!=GRANTEE
)
;

--Retrieve older DDL/query from history

SELECT   * 
FROM "SNOWFLAKE"."ACCOUNT_USAGE"."QUERY_HISTORY"
WHERE QUERY_TEXT ilike '%SEARCH_STRING%'
ORDER BY END_TIME desc limit 100
;

--Cancel a snowflake process
SELECT SYSTEM$CANCEL_QUERY('01b413d6-0101-35ef-0000-08e1123d8286')
;

Create role:
*/
USE ROLE ACCOUNTADMIN
;
CREATE ROLE <roleName>;

--THe above only creates a role. This role won't have any access
--To make a role usable, it needs to be granted to a user
--Grant role to user:
GRANT ROLE <roleName> TO USER <userName>;

--The user can use the new role with above. However, the user won't be able to use any warehouse
--To make a user use the new role with a warehouse we need to GRANT USAGE on warehouse:
GRANT USAGE ON WAREHOUSE <warehouseName> TO ROLE <roleName>;

--To make the role access a schema:
GRANT USAGE ON SCHEMA <schemaName> TO ROLE <roleName>;

--To make the role access a table in above SCHEMA
GRANT SELECT ON ALL TABLES IN SCHEMA <schemaName> TO ROLE <roleName>;

--A role can be granted to another role:
GRANT ROLE <role1> TO ROLE <role2>;
