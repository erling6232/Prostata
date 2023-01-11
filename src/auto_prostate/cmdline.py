"""Command-line programs
"""

# Copyright (c) 2023 Erling Andersen, Haukeland University Hospital, Bergen, Norway

import platform
import logging
import argparse
from datetime import date, timedelta
import pynetdicom.sop_class
import pynetdicom.presentation
from .query import connect, cfind_studies
from .database import create_database, get_db_record, set_db_record
from .python_mysql_dbconfig import read_config


logger = logging.getLogger(__name__)


presentation_contexts = [pynetdicom.sop_class.MRImageStorage]


def search_studies(assoc, date_range, study_search):
    patient_id = ''
    studies = cfind_studies(assoc, patient_id, date_range, study_search)


def search():
    """Search for study using DICOM Query/Retrieve.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', '-c',
                        help='Configuration file', default='auto-prostate.ini')
    # parser.add_argument("in_dirs",  # nargs='+',
    #                     help="Input directories and files")
    args = parser.parse_args()

    # Read configuration file
    config = read_config(filename=args.config)
    if 'mysql' in config:
        db_config = config['mysql']
    else:
        raise ValueError('No [mysql] section found in {}'.format(args.config))
    if 'pacs' in config:
        pacs_config = config['pacs']
    else:
        raise ValueError('No [pacs] section found in {}'.format(args.config))

    # Get PACS search parameters
    host = pacs_config['host']
    port = pacs_config['port']
    aet = pacs_config['aet']
    study_search = pacs_config['studydescription']
    date_range = "{}-".format(
        (date.today() + timedelta(days=pacs_config['daterange'])).strftime("%Y%m%d")
    )
    print('PACS search parameters:')
    print('  Host: {}\n  Port: {}\n  AET: {}'.format(host, port, aet))
    print('  Study search: {}\n  Date range: {}'.format(study_search, date_range))

    # Search PACS for studies
    assoc = connect(host, port, aet)
    studies = search_studies(assoc, date_range, study_search)
    assoc.release()
    print('Studies found: {}'.format(len(studies)))

    # Compare studies to database and update
    db = connect(db_config=db_config)
    cursor = db.cursor()

    for study in studies:
        print('{}\n'.format(study))
        try:
            record = get_db_record(cursor, study.StudyInstanceUID)
            print('Compare to: {}'.format(record))
        except:
            record = {
                'stuinsuid': study.StudyInstanceUID,
                'studyid': study.StudyID,
                'studydate': study.StudyDate,
                'studytime': study.StudyTime,
                'studydescr': study.StudyDescription,
                'bodypartex': study.BodyPartExamined,
                'accno': study.AccessionNumber,
                'status': 'detected',
                'series': study.NumberOfSeriesReceived,
                'images': study.NumberOfImagesReceived
            }
        set_db_record(db, cursor, record)



    cursor.close()
    db.close()


def initialize():
    """Initialize database.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', '-c',
                        help='Configuration file', default='auto-prostate.ini')
    # parser.add_argument("in_dirs",  # nargs='+',
    #                     help="Input directories and files")
    args = parser.parse_args()

    db_config = read_db_config(filename=args.config, section='mysql')

    cnx = create_database(db_config=db_config)
