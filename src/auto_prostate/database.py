"""Database utilities
"""


import mysql.connector
from mysql.connector import errorcode, Error


TABLES = {}
TABLES['studies'] = (
    "CREATE TABLE IF NOT EXISTS `studies` ("
    "  `stuinsuid` varchar(14) NOT NULL,"
    "  `studyid` varchar(14) NOT NULL,"
    "  `studydate` varchar(14) NOT NULL,"
    "  `studytime` varchar(14) NOT NULL,"
    "  `studydescr` varchar(14) NOT NULL,"
    "  `bodypartex` varchar(14) NOT NULL,"
    "  `accno` varchar(14) NOT NULL,"
    "  `status` varchar(14) NOT NULL,"
    "  `series` int(11) NOT NULL,"
    "  `images` int(11) NOT NULL,"
    "  PRIMARY KEY (`stuinsuid`)"
    ") ENGINE=InnoDB")
STUDIES_COLUMNS = "stuinsuid,studyid,studydate,studytime,studydescr,bodypartex"\
                  "accno,status,series,images"


def connect(db_config):
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

    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor()
    try:
        cursor.execute(
            "CREATE DATABASE {} DEFAULT CHARACTER SET 'utf8'".format(db_config['database']))
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_DB_CREATE_EXISTS:
            print("Database {} created successfully.".format(db_config['database']))
        else:
            print("Failed creating database: {}".format(err))
            exit(1)

    try:
        cursor.execute("USE {}".format(db_config['database']))
    except mysql.connector.Error as err:
        print("Database {} does not exists.".format(db_config['database']))
        if err.errno == errorcode.ER_BAD_DB_ERROR:
            create_database(cursor)
            print("Database {} created successfully.".format(db_config['database']))
            cnx.database = db_config['database']
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
        record (dict) - study record
    Raises:
        IndexError - when studyInstanceUID is not present
    """

    record = None
    try:
        cursor.execute("SELECT {} FROM studies WHERE stuinsuid = {}".format(
            STUDIES_COLUMNS, studyInstanceUID))
    except mysql.connector.Error:
        raise IndexError('StudyInstanceUID {} not present'.format(
            studyInstanceUID
        ))
    if cursor.rowcount > 0:
        record = {}
        for c, i in enumerate(STUDIES_COLUMNS.split(',')):
            record[c] = cursor[0][i]
    return record


def set_db_record(db, cursor, record):
    """Set database record for given StudyInstanceUID."""

    args = []
    for c in STUDIES_COLUMNS.split(','):
        args.append(c)
    try:
        # Verify whether studyInstanceUID already exists
        cursor.execute("SELECT stuinsuid FROM studies "
                       "WHERE stuinsuid = {}".format(record['stuinsuid']))
        if cursor.rowcount > 0:
            # Set new record in database
            cursor.execute("INSERT INTO studies ({}) "
                           "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)".format(STUDIES_COLUMNS),
                           args)
            db.commit()
        else:
            # Update record in database
            cursor.execute("UPDATE studies "
                           "SET studyid=%s, studydate=%s, studytime=%s, "
                           "studydescr=%s, bodypartex=%s, accno=%s, "
                           "status=%s, series=%s, images=%s "
                           "WHERE stuinsuid = {}".format(
                               record['stuinsuid']
                           ),
                           args[1:])
            db.commit()
    except mysql.connector.Error:
        raise
