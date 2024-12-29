// Use DBML to define your database structure
// Docs: https://dbml.dbdiagram.io/docs

Table audit_application {
  application_id integer [primary key]
  application_name varchar
  application_desc varchar
  status varchar
  created_date date
  created_by varchar
}

Table audit_app_task {
  application_id integer [primary key]
  task_id integer [primary key]
  task_name varchar
  task_desc varchar
  status varchar
  created_date date
  created_by varchar
}

Table audit_batch_log {
  batch_id integer [primary key]
  application_id integer [primary key]
  batch_start_time datetime
  batch_end_time datetime
  status varchar
  created_date date
  created_by varchar
  last_upd_time datetime
  last_upd_by varchar
}

Table audit_batch_control {
  batch_id integer [primary key]
  application_id integer [primary key]
  task_id integer [primary key]
  task_start_time datetime
  task_end_time datetime
  status varchar
  source_record_count integer
  target_record_count integer
  created_time datetime
  created_by varchar
}


Ref: audit_app_task.application_id > audit_application.application_id

Ref: audit_batch_log.application_id > audit_application.application_id

Ref: audit_batch_control.(batch_id, application_id) > audit_batch_log.(batch_id, application_id)

Ref: audit_batch_control.(application_id, task_id) > audit_app_task.(application_id, task_id)
