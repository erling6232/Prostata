"""Command-line programs
"""

# Copyright (c) 2023 Erling Andersen, Haukeland University Hospital, Bergen, Norway

import logging
import argparse
from datetime import date, timedelta
import pynetdicom.sop_class
import pynetdicom.presentation
from .query import connect, cfind_studies, cmove_study
from .database import db_connect, create_database, get_db_record, set_db_record
from .python_mysql_dbconfig import read_config, read_db_config


logger = logging.getLogger(__name__)


presentation_contexts = [pynetdicom.sop_class.MRImageStorage]


def search():
    """Search for study using DICOM Query/Retrieve.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', '-c',
                        help='Configuration file', default='auto-prostate.ini')
    parser.add_argument('--dry', action='store_true',
                        help='Dry-run', default=None)
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
    port = int(pacs_config['port'])
    aet = pacs_config['aet']
    institutions = pacs_config['institutions'].split(', ')
    study_search = pacs_config['studydescription']
    date_range = "{}-{}".format(
        (date.today() + timedelta(days=int(pacs_config['daterange']))).strftime("%Y%m%d"),
        date.today().strftime("%Y%m%d")
    )
    patient_id = ''
    print('PACS search parameters:')
    print('  Host: {}\n  Port: {}\n  AET: {}'.format(host, port, aet))
    print('  Institutions: {}'.format(institutions))
    print('  Study search: {}\n  Date range: {}'.format(study_search, date_range))

    # Search PACS for studies
    assoc = connect(host, port, aet)
    studies = []
    for institution in institutions:
        print('Search institution {}'.format(institution))
        try:
            studies += cfind_studies(assoc, institution, patient_id, date_range, study_search)
        except ConnectionError as e:
            print('{}'.format(e))
    assoc.release()
    print('Studies found: {}'.format(len(studies)))

    # Remove duplicates
    studies = sanitize_studies(studies)
    print('Studies after sanitization: {}'.format(len(studies)))

    # Compare studies to database and update
    db = db_connect(db_config)
    cursor = db.cursor()

    inserted = updated = 0

    todo = []
    for study in studies:
        print('Lookup: {}\n'.format(study.StudyInstanceUID))
        record = get_db_record(cursor, study.StudyInstanceUID)
        if record is None:
            record = record_from_dataset(study)
            if record['images'] > 0:
                print('Insert: {}'.format(record['stuinsuid']))
                set_db_record(db, cursor, record)
                inserted += 1
        else:
            print('Compare : {}'.format(record['stuinsuid']))
            new_record = record_from_dataset(study)
            modified_record = None
            try:
                modified_record = handle_difference(record, new_record, todo)
            except ValueError as e:
                print('{}\nDB record:\n{}\nPresent record:\n{}'.format(
                    e, record, new_record
                ))
            if modified_record is not None:
                set_db_record(db, cursor, modified_record)
                updated += 1

    print('Inserted: {}, updated {}'.format(inserted, updated))
    print('Todo list: {}'.format(len(todo)))
    for task in todo:
        print('operation: {} {}'.format(
            task['operation'],
            task['study']['status']
        ))
        # new_record = difference(record, new_record)
        if not args.dry:
            task['operation'](task['study'], config)

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

    _ = create_database(db_config=db_config)


def sanitize_studies(my_input):
    studies = []
    uids = {}
    for study in my_input:
        if study.StudyInstanceUID not in uids:
            studies.append(study)
            uids[study.StudyInstanceUID] = True
    return studies


def record_from_dataset(ds):
    return {
        'stuinsuid': str(ds.StudyInstanceUID),
        'studyid': ds.StudyID,
        'studydate': ds.StudyDate,
        'studytime': ds.StudyTime,
        'studydescr': ds.StudyDescription,
        'bodypartex': ds.BodyPartExamined,
        'accno': ds.AccessionNumber,
        'status': 'detected',
        'series': int(ds.NumberOfStudyRelatedSeries),
        'images': int(ds.NumberOfStudyRelatedInstances)
    }


def handle_difference(record1, record2, todo):
    if record1['stuinsuid'] != record2['stuinsuid']:
        raise ValueError('not_same_study')
    if record1['studyid'] != record2['studyid']:
        raise ValueError('not_same_study')
    if record1['studydate'] != record2['studydate']:
        raise ValueError('not_same_date')
    if record1['studytime'] != record2['studytime']:
        raise ValueError('not_same_time')
    if record1['studydescr'] != record2['studydescr']:
        raise ValueError('not_same_descr')
    if record1['bodypartex'] != record2['bodypartex']:
        raise ValueError('not_same_bodypart')
    if record1['accno'] != record2['accno']:
        raise ValueError('not_same_accno')
    if record1['series'] < record2['series']:
        return None
    if record1['images'] < record2['images']:
        return None

    if record1['status'] == 'detected':
        # No change since last check => stable state
        record2['status'] = 'stable'
        # Add this study to the C-MOVE todo list
        todo.append({
            'operation': cmove_record,
            'study': record2
        })
        return record2
    return None


def cmove_record(record, config):

    print('cmove_record {} {}'.format(
        config['store']['cmove'],
        record['stuinsuid']
    ))

    assoc = connect(
        config['pacs']['host'],
        config['host']['port'],
        config['host']['aet']
    )
    cmove_study(assoc,
                config['store']['cmove'],
                record['stuinsuid']
                )
    assoc.release()
