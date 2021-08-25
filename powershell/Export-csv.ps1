Get-Date
$SQLSERVER="xxxxxx"
$SQLDB="xxxx"
$UID="xxxxxxx"
$PWD="xxxxxxxx"
$DELIMITER=","
$SQLQUERY="SELECT agid ,sessnum ,active ,csvid ,visitstatus ,patientid ,CONVERT(NVARCHAR(20),visitdate,120) as VisitDate ,visitnumber ,epiid ,medrecord ,firstname ,lastname ,address ,city ,county ,state ,zip ,homephone ,sex ,CONVERT(NVARCHAR(20),dob,120) as DOB ,svccode ,directions ,physid ,pharmname ,pharmphone ,reasoncodeid ,CONVERT(NVARCHAR(20),reasoncodedate,120) as REASONCODEDATE ,reschedindays ,startodo ,endodo ,CONVERT(NVARCHAR(20),soc,120) as SOC ,mi ,nickname ,ssn ,workphone ,altphone ,email ,evaldisc ,newordertypeid ,medreleasecode ,admissionsource ,dcstatus ,dccondition ,signatureby ,caregiverreason ,CONVERT(NVARCHAR(20),hospadmitdate,120) as HOSPADMITDATE ,CONVERT(NVARCHAR(20),hospdcdate,120) as HOSPDCDATE ,hospreason ,altphysid ,raceid ,billable ,hospitalname ,CONVERT(NVARCHAR(20),episodestartdate,120) as EPISODESTARTDATE ,CONVERT(NVARCHAR(20),episodeenddate,120) as EPISODEENDDATE ,facilitytype ,hospmrnumber ,newepiid ,CONVERT(NVARCHAR(20),starttime,120) as STARTTIME ,CONVERT(NVARCHAR(20),endtime,120) as ENDTIME ,tripfees ,mileagepaymethod ,medidsource ,CONVERT(NVARCHAR(20),insertdate,120) as INSERTDATE ,CONVERT(NVARCHAR(20),processeddate,120) as PROCESSEDDATE ,serviceline ,slfloor ,slroom ,slcomments ,unabletocollectallvs ,CONVERT(NVARCHAR(20),VSOC,120) as VSOC ,intakeheight ,intakeweight ,abnanswer ,mdid ,CONVERT(NVARCHAR(20),datetimeofdeath,120) as DATETIMEOFDEATH ,casemanagerid ,episodetiming ,CompletionRequired ,EpisodeTimingChanged ,latevisit ,SetSocDateFlag ,EnableHospiceInPatientEncounter ,earlierbillablevisit ,takegpsatvisitstart ,takegpsatvisitend ,medconsultbypharmacy ,TotalCareMinutes ,fsheaderid ,DemographicsChanges ,TherapyReassessmentType ,ICDCodeVersionID ,dcreasonid ,SchemaVersion ,CaregiverSignatureContact FROM HCHB.dbo.PC_PATIENTS1"
$SQLCONN=New-Object System.Data.SqlClient.SqlConnection
$SQLCONN.ConnectionString="Server=$SQLSERVER; Database=$SQLDB; User ID=$UID; Password=$PWD"
$SqlCmd=New-Object System.Data.SqlClient.SqlCommand
$SqlCmd.CommandText = $SQLQUERY
$SqlCmd.Connection = $SQLCONN
$SqlAdapter = New-Object System.Data.SqlClient.SqlDataAdapter
$SqlAdapter.SelectCommand = $SqlCmd
$DataSet = New-Object System.Data.DataSet
$SqlAdapter.Fill($DataSet)
$DataSet.Tables[0] | export-csv -Delimiter $DELIMITER -Path "C:\Documents\dataFiles\PC_PATIENTS1.csv" -NoTypeInformation
$SQLCONN.Close()
Get-Date
