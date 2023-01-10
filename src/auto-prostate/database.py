"""Database utilities
"""


from mysql.connector import MySQLConnection, Error, errorcode
from python_mysql_dbconfig import read_db_config


def connect(db_config=None):
    """Connect to database"""

    if db_config is None:
        db_config = read_db_config()
    conn = None
    try:
        conn = MySQLConnection(**db_config, buffered=True)
    except Error as error:
        if error.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            raise IOError('Wrong database user name or password')
        elif error.errno == errorcode.ER_BAD_DB_ERROR:
            raise IOError('Database does not exist')
        raise
    return conn


