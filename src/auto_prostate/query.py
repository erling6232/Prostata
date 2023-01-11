import logging
import platform
import pydicom
import pydicom.datadict
import pynetdicom
import pynetdicom.sop_class


logger = logging.getLogger(__name__)


def connect(hostname, port, aet):
    """Search for study using DICOM Query/Retrieve.
    """

    try:
        _localhost = platform.node()
        local_aet = _localhost.split('.')[0]
    except IndexError:
        local_aet = 'IMAGEDATA'


    logger.debug("DicomTransport search calling AET: {}".format(local_aet))
    ae = pynetdicom.AE(ae_title=local_aet)
    ae.requested_contexts = pynetdicom.presentation.QueryRetrievePresentationContexts
    ae.add_requested_context(pynetdicom.sop_class.StudyRootQueryRetrieveInformationModelGet)
    ae.add_requested_context(pynetdicom.sop_class.MRImageStorage)
    ae.add_requested_context(pynetdicom.sop_class.StudyRootQueryRetrieveInformationModelMove)

    assoc = ae.associate(hostname, port, ae_title=aet)
    if not assoc.is_established:
        raise
    return assoc


def cfind_studies(assoc, institution, patient_id, date_range, search_term):

    # Create our Identifier (query) dataset
    ds = pydicom.dataset.Dataset()
    ds.QueryRetrieveLevel = 'STUDY'
    ds.StudyDescription = search_term
    ds.InstitutionName = institution
    # ds.PatientName = ''
    # ds.PatientID = ''
    ds.BodyPartExamined = ''
    ds.StudyInstanceUID = ''
    ds.StudyDate = date_range
    ds.StudyTime = ''
    ds.AccessionNumber = ''
    ds.NumberOfStudyRelatedSeries = ''
    ds.NumberOfStudyRelatedInstances = ''

    instances = \
        cfind(assoc, ds,
                    pynetdicom.sop_class.StudyRootQueryRetrieveInformationModelFind,
                    'StudyInstanceUID')
    # pynetdicom.sop_class.PatientRootQueryRetrieveInformationModelFind,
    return instances


def cfind(assoc, ds, model, tag):
    # Associate with the peer AE
    if assoc.is_established:
        # Send the C-FIND request
        responses = assoc.send_c_find(ds, model)
        instances = []
        for (status, identifier) in responses:
            if status:
                if identifier is not None:
                    # uid = identifier[tag].value
                    instances.append(identifier)
                    # __catalog[uid] = identifier
            else:
                raise ConnectionError(
                    'Connection timed out, was aborted or received invalid response')
        return instances
    else:
        raise ConnectionError('Association rejected, aborted or never connected')

def cmove_study(assoc, destination, study_instance_uid):
    # Create our Identifier (query) dataset
    # We need to supply a Unique Key Attribute for each level above the
    #   Query/Retrieve level
    ds = pydicom.dataset.Dataset()
    ds.QueryRetrieveLevel = 'STUDY'
    # Unique key for STUDY level
    ds.StudyInstanceUID = study_instance_uid

    if assoc.is_established:
        # Use the C-MOVE service to send the identifier
        responses = assoc.send_c_move(
            ds,
            destination,
            pynetdicom.sop_class.StudyRootQueryRetrieveInformationModelMove)
        for (status, identifier) in responses:
            if status:
                print('C-MOVE query status: 0x{0:04x}'.format(status.Status))
            else:
                print('Connection timed out, was aborted or received invalid response')
    else:
        raise ConnectionError('Association rejected, aborted or never connected')

def cget_series(self, destdir, study_instance_uid, series_instance_UID):
    raise ValueError('Not tested')
    handlers = [(pynetdicom.evt.EVT_C_STORE, self._handle_store)]

    # # Initialise the Application Entity
    ae = pynetdicom.AE(ae_title=self.__local_aet)

    ae.add_requested_context(pynetdicom.sop_class.StudyRootQueryRetrieveInformationModelGet)
    # Add the requested presentation contexts (Storage SCP)
    roles = []
    for storage_class in presentation_contexts:
        # Add the requested presentation contexts (QR SCU)
        ae.add_requested_context(storage_class)
        # Create an SCP/SCU Role Selection Negotiation item for CT Image Storage
        roles.append(pynetdicom.build_role(storage_class, scp_role=True))

    # Create our Identifier (query) dataset
    # We need to supply a Unique Key Attribute for each level above the
    #   Query/Retrieve level
    ds = pydicom.dataset.Dataset()
    ds.QueryRetrieveLevel = 'SERIES'
    # Unique key for SERIES level
    ds.SeriesInstanceUID = series_instance_UID

    # Associate with peer AE at IP 127.0.0.1 and port 11112
    assoc = ae.associate(self.__host, self.__port, ae_title=self.__aet,
                         ext_neg=roles, evt_handlers=handlers)

    if assoc.is_established:
        # Use the C-GET service to send the identifier
        responses = assoc.send_c_get(
            ds, pynetdicom.sop_class.StudyRootQueryRetrieveInformationModelGet)
        for (status, identifier) in responses:
            if status:
                pass
            else:
                raise ConnectionError(
                    'Connection timed out, was aborted or received invalid response')

        # Release the association
        assoc.release()
    else:
        raise ConnectionError('Association rejected, aborted or never connected')

