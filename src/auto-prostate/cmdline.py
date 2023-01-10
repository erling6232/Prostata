"""Command-line programs
"""

# Copyright (c) 2023 Erling Andersen, Haukeland University Hospital, Bergen, Norway

import platform
import logging
import pynetdicom.sop_class
import pynetdicom.presentation
from query import connect, cfind_studies


logger = logging.getLogger(__name__)


presentation_contexts = [pynetdicom.sop_class.MRImageStorage]


hostname = 'SectraDCMImport.ihelse.net'
port = 7840
aet = 'DICOM_QR_SCP'
study_search = '*Prostata*'


def search():
    """Search for study using DICOM Query/Retrieve.
    """

    assoc = connect(hostname, port, aet)

    patient_id = ''
    studies = cfind_studies(assoc, patient_id, study_search)
    print('Studies found: {}'.format(len(studies)))
    for study in studies:
        print('{}\n'.format(study))
    assoc.release()


if __name__ == '__main__':
    search()