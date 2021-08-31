--To check running process
SELECT pid, age(clock_timestamp(), query_start), usename, query, state, p.* 
FROM pg_stat_activity as p
WHERE query != '<IDLE>' AND query NOT ILIKE '%pg_stat_activity%' 
--and query like 'COPY %'
;
