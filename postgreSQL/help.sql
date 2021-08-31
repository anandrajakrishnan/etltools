--To check running process
SELECT pid, age(clock_timestamp(), query_start), usename, query, state, p.* 
FROM pg_stat_activity as p
WHERE query != '<IDLE>' AND query NOT ILIKE '%pg_stat_activity%' 
--and query like 'COPY %'
;
--get column metadata
SELECT *
FROM information_schema.columns
where table_schema in ('xxxxx')
and table_name='xxxxxxxx'
;
--Get table size
select pg_size_pretty(pg_relation_size('schema.table'));
SELECT split_part(pg_size_pretty(pg_relation_size('schema.table')),' ',1)::real/1024;
--Get version of DB
select current_database();
