"""Database utilities
"""


import mysql.connector
from mysql.connector import errorcode, Error


TABLES = {}
TABLES['studies'] = (
    "CREATE TABLE IF NOT EXISTS `studies` ("
    "  `stuinsuid` varchar(64) NOT NULL,"
    "  `studyid` varchar(16) NOT NULL,"
    "  `studydate` varchar(10) NOT NULL,"
    "  `studytime` varchar(10) NOT NULL,"
    "  `studydescr` varchar(64) NOT NULL,"
    "  `bodypartex` varchar(16) NOT NULL,"
    "  `accno` varchar(16) NOT NULL,"
    "  `status` varchar(16) NOT NULL,"
    "  `series` int(11) NOT NULL,"
    "  `images` int(11) NOT NULL,"
    "  PRIMARY KEY (`stuinsuid`)"
    ") ENGINE=InnoDB")
STUDIES_COLUMNS = "stuinsuid,studyid,studydate,studytime,studydescr,bodypartex,"\
                  "accno,status,series,images"


def db_connect(db_config):
    """Connect to database"""

    try:
        conn = mysql.connector.MySQLConnection(**db_config, buffered=True)
    except Error as error:
        if error.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            raise IOError('Wrong database user name or password')
        elif error.errno == errorcode.ER_BAD_DB_ERROR:
            raise IOError('Database does not exist')
        raise
    return conn


def create_database(db_config):
    """Create database"""

    database = db_config['database']
    del db_config['database']

    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()
    try:
        cursor.execute(
            "CREATE DATABASE {} DEFAULT CHARACTER SET 'utf8'".format(database))
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_DB_CREATE_EXISTS:
            print("Database {} created successfully.".format(database))
        else:
            print("Failed creating database: {}".format(err))
            exit(1)

    try:
        cursor.execute("USE {}".format(database))
    except mysql.connector.Error as err:
        print("Database {} does not exists.".format(database))
        if err.errno == errorcode.ER_BAD_DB_ERROR:
            create_database(cursor)
            print("Database {} created successfully.".format(database))
            cnx.database = database
        else:
            print(err)
            exit(1)

    for table_name in TABLES:
        table_description = TABLES[table_name]
        try:
            print("Creating table {}: ".format(table_name), end='')
            cursor.execute(table_description)
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
                print("already exists.")
            else:
                print(err.msg)
        else:
            print("OK")

    cursor.close()
    cnx.close()


def get_db_record(cursor, studyInstanceUID):
    """Get database record for given StudyInstanceUID.

    Arg:
        cursor
        studyInstanceUID
    Returns:
        record (dict) - study record, None if none is found
    Raises:
        mysql.connector.Error
    """

    record = None
    try:
        cursor.execute("SELECT {} FROM studies WHERE stuinsuid = '{}'".format(
            STUDIES_COLUMNS, studyInstanceUID))
    except mysql.connector.Error:
        raise
    if cursor.rowcount > 0:
        for row in cursor:
            record = {}
            for i, c in enumerate(STUDIES_COLUMNS.split(',')):
                record[c] = row[i]
    return record


def set_db_record(db, cursor, record):
    """Set database record for given StudyInstanceUID."""

    args = []
    for c in STUDIES_COLUMNS.split(','):
        args.append(c)
    try:
        # Verify whether studyInstanceUID already exists
        cursor.execute("SELECT stuinsuid FROM studies "
                       "WHERE stuinsuid = '{}'".format(record['stuinsuid']))
        print('set_db_record: cursor.rowcount {}'.format(cursor.rowcount))
        if cursor.rowcount < 1:
            # Set new record in database
            result = cursor.execute("INSERT INTO studies ({}) "
                           "VALUES (%(stuinsuid)s,%(studyid)s,%(studydate)s,%(studytime)s"
                           ",%(studydescr)s,%(bodypartex)s,%(accno)s,%(status)s,%(series)s"
                           ",%(images)s)".format(STUDIES_COLUMNS),
                           record)
            db.commit()
        else:
            # Update record in database
            result = cursor.execute("UPDATE studies "
                           "SET studyid=%(studyid)s, "
                           "studydate=%(studydate)s, studytime=%(studytime)s, "
                           "studydescr=%(studydescr)s, bodypartex=%(bodypartex)s, "
                           "accno=%(accno)s, "
                           "status=%(status)s, series=%(series)s, images=%(images)s "
                           "WHERE stuinsuid=%(stuinsuid)s",
                           record)
            db.commit()
    except mysql.connector.Error:
        raise
