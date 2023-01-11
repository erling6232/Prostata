from configparser import ConfigParser


def read_db_config(filename='auto_prostate.ini', section='mysql'):
    """Read database configuration file and return a dictionary object
    :param filename: name of the configuration file
    :param section: section of database configuration
    :return: a dictionary of database parameters
    """

    # Create parser and read ini configuration file
    parser = ConfigParser()
    parser.read(filename)

    # Get section, default to mysql
    db = {}
    if parser.has_section(section):
        items = parser.items(section)
        for item in items:
            db[item[0]] = item[1]
    else:
        raise Exception('{0} not found in the {1} file'.format(section, filename))

    return db


def read_config(filename='auto_prostate.ini'):
    """Read database configuration file and return a dictionary object
    :param filename: name of the configuration file
    :return: a dictionary of parameters
    """

    # Create parser and read ini configuration file
    parser = ConfigParser()
    parser.read(filename)

    config = {}
    # For each section
    for section in parser.sections():
        config[section] = {}
        items = parser.items(section)
        for item in items:
            config[section][item[0]] = item[1]

    return config
