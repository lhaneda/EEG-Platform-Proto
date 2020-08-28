import psycopg2
from configLCL import BoxRoot
import configLCL

rndlist = [u'apprehension', u'works', u'reconfigurations', u'drum', u'multiplications', u'jobs', u'entrance', u'replenishments', u'force', u'edge', u'shop', u'benefits', u'clamp', u'legs', u'foreground', u'hook', u'substitutes', u'driver', u'buffers', u'hotels', u'darts', u'circuitry', u'allotment', u'metal', u'hoofs', u'similarities', u'diamonds', u'pines', u'horn', u'second', u'subfunction', u'capstan', u'seasons', u'shades', u'towns', u'dip', u'dolly', u'writers', u'motion', u'loaf', u'gleam', u'harmonies', u'top', u'atom', u'transit', u'glow', u'emitters', u'science', u'riddles', u'magnets', u'blurs', u'abbreviation', u'deserts', u'centimeters', u'nature', u'projects', u'december', u'deficiencies', u'chip', u'accounting', u'divider', u'editors', u'outing', u'algorithm', u'autos', u'firer', u'seawater', u'car', u'coder', u'vices', u'leap', u'partner', u'fogs', u'masters', u'doorstep', u'lookouts', u'drains', u'hyphen', u'blueprint', u'behaviors', u'obligations', u'acquisition', u'powder', u'clay', u'secretary', u'starboard', u'suppressions', u'skills', u'weld', u'shifts', u'radios', u'specialty', u'rescue', u'loop', u'groove', u'bureau', u'briefing', u'ignition', u'augmentations', u'oscillations']
rndlist = [x.encode('ascii') for x in rndlist if len(x) >= 6 and len(x) <= 8]

### AWS Information
### Master username

aUser = 'drnick'
apass = 'sqlClass20172'
adbname = 'sqlcert'
ahost = 'sqlcert2018.c3ogcwmqzllz.us-east-1.rds.amazonaws.com'

namelist = [
['Yim ', 'Ken ']
,['Thahar', 'Aldrich ']
,['Rodriguez', 'Claudia ']
,['Pucci ', 'Tamara']
,['Popovic', 'Karla']
,['Thomas ', 'Zachary ']
,['Santos', 'Rocel']
,['Gears', 'Grantland']
,['Cruz Garcia', 'Nestor']
,['Barnhorst', 'Keener']
,['Reichmann ', 'Lara']
,['Ogudu', 'Chimere']
,['Bellavy', 'Ros']
,['Kelly', 'Gola']
,['Tandon', 'Deepali']
,['Ross', 'Lauren']
,['Wang', 'Oliver']
,['Barnes', 'Kimberly']
,['Padilla', 'Daniel']
,['Lerit', 'Janice']
,['Siripurapu', 'Anitha']
,['Ye ', 'Yun ']
,['Fagar ', 'Jayson ']
,['Promsookt', 'Poranas']
,['Pental', 'Bikramjit']
,['Qin ', 'Lydia ']
,['Kavanagh', 'William']
, ['Edith', 'Cabrera']
]

### Create username list:
unamelist=  [x[1].replace(' ', '').lower() + x[0][0:2].lower() for x in namelist]
unamelist = zip( unamelist, rndlist)


unamelist = [(x[0], x[1].decode().title() + '%d' % len(x[0])) for x in unamelist]

finallist = []
for x in range(0, len(unamelist)):
    finallist.append( namelist[x][1] + ' ' + namelist[x][0] + '  Username: ' + unamelist[x][0] + ' Password: ' + unamelist[x][1])

print('\n'.join(finallist))

### connect to the server
## Flag for running local or on the SQL server
runlocal = 0

if runlocal:
    Sconn = psycopg2.connect(configLCL.LCLPostString)
else:
    conn_string = "host='%s' dbname='%s' user='%s' password='%s'" % (ahost, adbname, aUser, apass)
    Sconn = psycopg2.connect(conn_string)

Scur = Sconn.cursor()

#conn_string = "host='%s' dbname='%s' user='%s' password='%s'" % (ahost, adbname, aUser, apass)
#Sconn = psycopg2.connect(conn_string)
#Scur = Sconn.cursor()


def resetuser( aconn, acur, namelist):
    for usr in unamelist:
    ## Reset users by first dropping and then creating them
        try:
            acur.execute(""" DROP USER %s;""" % usr[0])
            aconn.commit()
        except psycopg2.ProgrammingError:
            print("CAUTION: Username not found: %s""" % usr[0])
            aconn.rollback()
    ### Create user

        try:
            #print("""CREATE USER %s with password '%s' """ % (usr[0], usr[1]))
            acur.execute("""CREATE USER %s with password '%s'; """ % (usr[0], usr[1]))
            aconn.commit()
        except psycopg2.ProgrammingError:
            print("CAUTION: USER CREATE %s failed" % usr[0])

    try:
        acur.execute( """CREATE GROUP STUDENTS;""")
        aconn.commit()
    except psycopg2.ProgrammingError:
        print("CAUTION: ")
        aconn.rollback()

    aconn.commit()

if 1 == 1:
    resetuser(Sconn, Scur, namelist) 

cmdlist1 = [
 """grant all on database sqlcert to group students;"""
,"""ALTER GROUP STUDENTS ADD USER %s;""" % ','.join( [u[0] for u in unamelist] )
, """CREATE SCHEMA cls;"""
    ,"""CREATE SCHEMA SP;"""
,    """CREATE SCHEMA stocks2016;"""

, """grant all on schema cls to group students;"""
, """grant all on schema SP to group students;"""
, """grant all on schema stocks2016 to group students;"""

, """ALTER DEFAULT PRIVILEGES IN SCHEMA cls GRANT SELECT ON TABLES TO PUBLIC;"""
, """ALTER DEFAULT PRIVILEGES IN SCHEMA sp GRANT SELECT ON TABLES TO PUBLIC;"""
, """ALTER DEFAULT PRIVILEGES IN SCHEMA stocks2016 GRANT SELECT ON TABLES TO PUBLIC;"""
    , """DROP TABLE stocks2016.d2010;"""
    , """DROP TABLE stocks2016.d2011;"""
    , """DROP TABLE stocks2016.lnk;"""
    , """DROP TABLE stocks2016.fnd;;"""
    , """DROP TABLE cls.cars cascade;"""
    , """DROP TABLE cls.mta;"""    
, """DROP TABLE cls.traffic;"""
, """create table stocks2016.d2010 (
	cusip varchar(8)
	, PERMNO bigint
	, PERMCO bigint
	, ISSUNO float
	, hsic float
	, retdate date
	, bid float
	, ask float
	, PRC float
	, VOL bigint
	, RET varchar(20)
	, SHROUT bigint);"""
, """create table stocks2016.d2011 (
	cusip varchar(8)
	, PERMNO bigint
	, PERMCO bigint
	, ISSUNO float
	, hsic float
	, retdate date
	, bid float
	, ask float
	, PRC float
	, VOL bigint
	, RET varchar(20)
	, SHROUT bigint);"""
, """create table stocks2016.fnd (
	gvkey varchar(8)
	, datadate date
	, fyear int
	, indfmr varchar(4)
	, consol varchar(1)
	, popsrc varchar(1)
	, datafmt varchar(3)
	, tic varchar(8)
	, cusip varchar(11)
	, conm varchar(30)
	, fyr int
	, cash float
	, dp float
	, ebitda float
	, emp float
	, invt float
	, netinc float
	, ppent float
	, rev float
	, ui float
	, cik varchar(10)
    );"""
, """create table stocks2016.lnk (
	gvkey varchar(8)
	, linkprim varchar(1)
	, liid varchar(4)
	, linktype varchar(4)
	, lpermno bigint
	, lpermco bigint
	, usedflag int
	, linkdt date
	, linkenddt varchar(10)
	);"""
    , """create table cls.cars (
    year int
    , yearending date
    , countyname varchar(20)
    , countycode int
    , motorvehicle varchar(3)
    , vehiclecat varchar(15)
    , vehicletype varchar(25)
    , tonnage  varchar(30)
    , registrations int
    , annualfee float
    , primarycountylat float
    , primarycountylong float
    , primarycountycord varchar(45)
);"""
,    """create table cls.traffic (
    districtID int
    , routeNo int
    , routeSuffix varchar(1)
    , county varchar(15)
    , postMilePrefix varchar(1)
    , postMileNo float
    , postMileSuffix varchar(1)
    , Des varchar(50)
    , SWPeakHr int
    , SWPeakMonthDay int
    , SWAvgDay int
    , NEPeakHr int
    , NEPeakMonthDay int
    , NEAvgDay int
    , location varchar(30)
);
    """
    ,  """grant all on cls.traffic to group students;"""

, """grant all on cls.cars to group students;"""
, """grant all on stocks2016.d2010 to group students;"""
, """grant all on stocks2016.d2011 to group students;"""
,"""grant all on stocks2016.lnk to group students;"""
,"""grant all on stocks2016.fnd to group students;"""
,

    """create table cls.mta (
                plaza int
                , mtadt date
                , hr int
                , direction varchar(1)
                , vehiclesEZ int
                , vehiclesCASH int );
    """
    , """grant all on cls.mta to group students;"""
]

cmds = cmdlist1

for x in cmds:
    try:
        Scur.execute(x)
        Sconn.commit()
    except psycopg2.ProgrammingError:
        print( """CAUTION FAILED: '%s' """ % x)
        Sconn.rollback()


SQL_STATEMENT = """
    COPY %s FROM STDIN WITH
        CSV
        HEADER
        DELIMITER AS E'\t';
    """

SQL_STATEMENT_C = """
    COPY %s FROM STDIN WITH
        CSV
        HEADER
        DELIMITER AS E',';"""

if 1 == 1:
    ### Note that the first file is CSV, the rest are TDF, which is why the loop below is broken down.
    filelist = [
        [BoxRoot + '/USF/Notes/SQLData/iowafleet2.csv', 'cls.cars']
        ,[BoxRoot + '/USF/LoadingData/Output/compm.tdf', 'stocks2016.fnd']
    ,    [BoxRoot + '/USF/LoadingData/Output/dsf2010.tdf', 'stocks2016.d2010']
    , [BoxRoot + '/USF/LoadingData/Output/dsf2011.tdf', 'stocks2016.d2011']
    , [BoxRoot + '/USF/LoadingData/Output/link.tdf', 'stocks2016.lnk']
     ]

    ### CSV:
    my_file = open(filelist[0][0])
    Scur.copy_expert(sql=SQL_STATEMENT_C % filelist[0][1], file = my_file)
    Sconn.commit()

    for x in filelist[1:]:
        print(x[1])
        my_file = open(x[0])
        Scur.copy_expert(sql=SQL_STATEMENT % x[1], file=my_file)
        Sconn.commit()

    filelist = [

        [BoxRoot + '/USF/Notes/SQLData/Caltrans_Traffic_Volumes_2014.csv', 'cls.traffic']

    ]

    for x in filelist:
        my_file = open(x[0])
        Scur.copy_expert(sql=SQL_STATEMENT_C % x[1], file=my_file)
        Sconn.commit()


    for x in [[BoxRoot +'/USF/Notes/SQLData/DataUpdate/NYMTA/MTA_Hourly.csv', 'cls.MTA']]:
        my_file = open(x[0])
        Scur.copy_expert(sql=SQL_STATEMENT_C % x[1], file=my_file)
        Sconn.commit()


## EOF##


