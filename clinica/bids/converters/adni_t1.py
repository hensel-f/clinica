
def adni1_image(subject_id, timepoint, visit_str, mprage_meta_subj, ida_meta_subj, mri_quality_subj):

    # Get the preferred scan (image series that has been Scaled)
    filtered_mprage = mprage_meta_subj[(mprage_meta_subj['Orig/Proc'] == 'Processed')
                                       & (mprage_meta_subj.Visit == visit_str)
                                       & (mprage_meta_subj.Sequence.map(lambda x: x.endswith('Scaled')))]

    # If there is not a preferred image we use ADNI2 processing (get the original) preferring 1.5T images
    if filtered_mprage.shape[0] < 1:
        mprage_meta_subj_orig = mprage_meta_subj[mprage_meta_subj['Orig/Proc'] == 'Original']
        return adni2_image(subject_id, timepoint, visit_str, mprage_meta_subj_orig, preferred_field_strength=1.5)



    filtered_mprage_mag = filtered_mprage
    if len(filtered_mprage.MagStrength.unique()) > 1:
        filtered_mprage_mag = filtered_mprage[filtered_mprage.MagStrength == 1.5]  # Select 1.5T images

    scan = filtered_mprage_mag.iloc[0]
    series_id = scan.SeriesID

    qc_passed = True

    qc = mri_quality_subj[mri_quality_subj.LONIUID == 'S' + str(scan.SeriesID)]
    if qc.shape[0] < 1:
        print 'QC ADNI 1 not found'
        print 'Subject ' + subject_id + ' - Series: ' + str(scan.SeriesID) + ' - Study: ' + str(scan.StudyID)
    else:
        if qc.iloc[0].PASS == 1:
            print 'QC found and passed'
        else:
            print 'QC found but NOT passed, NONONONO'
            print 'Subject ' + subject_id + ' - Series: ' + str(scan.SeriesID) + ' - Study: ' + str(scan.StudyID)
            mprage_meta_subj_alt = mprage_meta_subj[(mprage_meta_subj['Orig/Proc'] == 'Original')
                                                     & (mprage_meta_subj.Visit == visit_str)
                                                     & (mprage_meta_subj.SeriesID != series_id)]
            print mprage_meta_subj_alt.shape[0]
            scan = mprage_meta_subj_alt.iloc[0]
            series_id = scan.SeriesID
            qc_passed = False




    filtered_scan = ida_meta_subj[ida_meta_subj.LONIUID == series_id]

    if filtered_scan.shape[0] < 1:
        # If no IDA_META for 1.5T try for 3T
        filtered_mprage_mag = filtered_mprage[filtered_mprage.MagStrength == 3.0]
        scan = filtered_mprage_mag.iloc[0]
        series_id = scan.SeriesID

        filtered_scan = ida_meta_subj[ida_meta_subj.LONIUID == series_id]

        if filtered_scan.shape[0] < 1:
            print 'NO IDA Meta: ' + subject_id + ' for visit ' + timepoint + ' - ' + visit_str
            return None

    original = True
    ida_scan = filtered_scan.iloc[0]
    if ida_scan.Scanner.find('Philips') > -1:

        scan = (mprage_meta_subj[
                    (mprage_meta_subj['Orig/Proc'] == 'Original') & (mprage_meta_subj.SeriesID == series_id)]).iloc[
            0]
        sequence = scan.Sequence

    else:  # scan already selected above
        sequence = scan.Sequence[:scan.Sequence.find('N3') - 2]
        original = False

    if not qc_passed:
        if scan.Sequence == 'MP-RAGE':
            sequence = 'MPR; GradWarp; B1 Correction'
        else: # 'MP-RAGE REPEAT'
            sequence = 'MPR-R; GradWarp; B1 Correction'
        print sequence


    sequence = replace_sequence_chars(sequence)

    qc = mri_quality_subj[mri_quality_subj.LONIUID == 'S' + str(scan.SeriesID)]
    if qc.shape[0] > 0 and qc.iloc[0].PASS != 1:
        print 'QC found but NOT passed, NONONONO'
        print 'Subject ' + subject_id + ' - Series: ' + str(scan.SeriesID) + ' - Study: ' + str(scan.StudyID)

    return {'Subject_ID': subject_id,
            'VISCODE': timepoint,
            'Visit': visit_str,
            'Sequence': sequence,
            'Scan_Date': scan.ScanDate,
            'Study_ID': str(scan.StudyID),
            'Series_ID': str(scan.SeriesID),
            'Field_Strength': scan.MagStrength,
            'Original': original}


def adni2_image(subject_id, timepoint, visit_str, mprage_meta_subj_orig, preferred_field_strength=3.0):

    cond_mprage = ((mprage_meta_subj_orig.Visit == visit_str) & mprage_meta_subj_orig.Sequence.map(lambda x: ((
                                                                                                              x.lower().find(
                                                                                                                  'mprage') > -1) | (
                                                                                                              x.lower().find(
                                                                                                                  'mp-rage') > -1) | (
                                                                                                              x.lower().find(
                                                                                                                  'mp rage') > -1)) & (
                                                                                                             x.find(
                                                                                                                 '2') < 0) & (
                                                                                                             x.lower().find(
                                                                                                                 'repeat') < 0)))

    cond_spgr = ((mprage_meta_subj_orig.Visit == visit_str) & mprage_meta_subj_orig.Sequence.map(
        lambda x: (x.lower().find('spgr') > -1) & (x.lower().find('acc') < 0) & (x.lower().find('repeat') < 0)))

    filtered_scan = mprage_meta_subj_orig[cond_mprage | cond_spgr]
    if filtered_scan.shape[0] < 1:

        # TODO Improve this code. Don't make a double verification for the whole condition.
        # Invert order of filtering: less to more restrictive, check for the repeated as for the MagStrength
        cond_mprage_rep = ((mprage_meta_subj_orig.Visit == visit_str) & mprage_meta_subj_orig.Sequence.map(
            lambda x: ((x.lower().find('mprage') > -1) | (x.lower().find('mp-rage') > -1) | (
            x.lower().find('mp rage') > -1)) & (x.find('2') < 0)))

        cond_spgr_rep = ((mprage_meta_subj_orig.Visit == visit_str) & mprage_meta_subj_orig.Sequence.map(
            lambda x: (x.lower().find('spgr') > -1) & (x.lower().find('acc') < 0)))

        filtered_scan = mprage_meta_subj_orig[cond_mprage_rep | cond_spgr_rep]
        if filtered_scan.shape[0] < 1:
            print 'NO MPRAGE Meta2: ' + subject_id + ' for visit ' + timepoint + ' - ' + visit_str
            return None

    if len(filtered_scan.MagStrength.unique()) > 1:
        filtered_scan = filtered_scan[
            filtered_scan.MagStrength == preferred_field_strength]  # Select preferred_field_strength images

    scan = filtered_scan.iloc[0]

    sequence = replace_sequence_chars(scan.Sequence)

    return {'Subject_ID': subject_id,
            'VISCODE': timepoint,
            'Visit': visit_str,
            'Sequence': sequence,
            'Scan_Date': scan.ScanDate,
            'Study_ID': str(scan.StudyID),
            'Series_ID': str(scan.SeriesID),
            'Field_Strength': scan.MagStrength,
            'Original': True}


def adnigo_image(subject_id, timepoint, visit_str, mprage_meta_subj, ida_meta_subj, mri_quality_subj, mayo_mri_qc_subj, original_phase):

    if original_phase == 'ADNI1':
        filtered_mprage = mprage_meta_subj[(mprage_meta_subj['Orig/Proc'] == 'Processed')
                                           & (mprage_meta_subj.MagStrength == 1.5)
                                           & (mprage_meta_subj.Visit == visit_str)
                                           & (mprage_meta_subj.Sequence.map(lambda x: x.endswith('Scaled')))]
        if filtered_mprage.shape[0] > 0:
            print 'Calling ADNI1 from ADNIGO'
            return adni1_image(subject_id, timepoint, visit_str, mprage_meta_subj, ida_meta_subj, mri_quality_subj)

    mprage_meta_subj_orig = mprage_meta_subj[mprage_meta_subj['Orig/Proc'] == 'Original']
    return adni2_image(subject_id, timepoint, visit_str, mprage_meta_subj_orig)


def visits_to_timepoints_t1(subject, mprage_meta_subj_orig, adnimerge_subj):
        from datetime import datetime
        from adni_utils import days_between

        mprage_meta_subj_orig = mprage_meta_subj_orig[mprage_meta_subj_orig['Visit'] != 'ADNI Baseline']

        visits = dict()

        unique_visits = list(mprage_meta_subj_orig.Visit.unique())

        pending_timepoints = []

        # We try to obtain the corresponding image Visit for a given VISCODE
        for adni_row in adnimerge_subj.iterrows():  # (adnimerge_subj[adnimerge_subj.FLDSTRENG.map(lambda x: x is not '')]).iterrows():
            visit = adni_row[1]
            if visit.ORIGPROT == 'ADNI2':
                if visit.VISCODE == 'bl':
                    preferred_visit_name = 'ADNI2 Screening MRI-New Pt'
                elif visit.VISCODE == 'm03':
                    preferred_visit_name = 'ADNI2 Month 3 MRI-New Pt'
                elif visit.VISCODE == 'm06':
                    preferred_visit_name = 'ADNI2 Month 6-New Pt'
                else:
                    year = str(int(visit.VISCODE[1:]) / 12)
                    preferred_visit_name = 'ADNI2 Year ' + year + ' Visit'
            else:
                if visit.VISCODE == 'bl':
                    if visit.ORIGPROT == 'ADNI1':
                        preferred_visit_name = 'ADNI Screening'
                    else:  # ADNIGO
                        preferred_visit_name = 'ADNIGO Screening MRI'
                elif visit.VISCODE == 'm03':  # Only for ADNIGO Month 3
                    preferred_visit_name = 'ADNIGO Month 3 MRI'
                else:
                    month = int(visit.VISCODE[1:])
                    if month < 54:
                        preferred_visit_name = 'ADNI1/GO Month ' + str(month)
                    else:
                        preferred_visit_name = 'ADNIGO Month ' + str(month)

            if preferred_visit_name in unique_visits:
                key_preferred_visit = (visit.VISCODE, visit.COLPROT, visit.ORIGPROT)
                if key_preferred_visit not in visits.keys():
                    visits[key_preferred_visit] = preferred_visit_name
                elif visits[key_preferred_visit] != preferred_visit_name:
                    print 'Multiple visits for one timepoint!'
                    print subject
                    print key_preferred_visit
                    print visits[key_preferred_visit]
                    print visit
                unique_visits.remove(preferred_visit_name)
                continue

            pending_timepoints.append(visit)

        # Then for images.Visit non matching the expected labels we find the closest date in visits list
        for visit in unique_visits:
            image = (mprage_meta_subj_orig[mprage_meta_subj_orig.Visit == visit]).iloc[0]
            min_db = 100000
            min_db2 = 0
            min_visit = None
            min_visit2 = None

            for timepoint in pending_timepoints:
                db = days_between(image.ScanDate, timepoint.EXAMDATE)
                if db < min_db:
                    min_db2 = min_db
                    min_visit2 = min_visit

                    min_db = db
                    min_visit = timepoint

            if min_visit is None:
                print 'No corresponding timepoint in ADNIMERGE for subject ' + subject + ' in visit ' + image.Visit
                print image
                continue

            if min_visit2 is not None and min_db > 90:
                print 'More than 60 days for corresponding timepoint in ADNIMERGE for subject ' + subject + ' in visit ' + image.Visit + ' on ' + image.ScanDate
                print 'Timepoint 1: ' + min_visit.VISCODE + ' - ' + min_visit.ORIGPROT + ' on ' + min_visit.EXAMDATE + ' (Distance: ' + str(
                    min_db) + ' days)'
                print 'Timepoint 2: ' + min_visit2.VISCODE + ' - ' + min_visit2.ORIGPROT + ' on ' + min_visit2.EXAMDATE + ' (Distance: ' + str(
                    min_db2) + ' days)'

                # If image is too close to the date between two visits we prefer the earlier visit
                if (datetime.strptime(min_visit.EXAMDATE, "%Y-%m-%d")
                        > datetime.strptime(image.ScanDate, "%Y-%m-%d")
                        > datetime.strptime(min_visit2.EXAMDATE, "%Y-%m-%d")):
                    dif = days_between(min_visit.EXAMDATE, min_visit2.EXAMDATE)
                    if abs((dif / 2.0) - min_db) < 30:
                        min_visit = min_visit2

                print 'We prefer ' + min_visit.VISCODE

            key_min_visit = (min_visit.VISCODE, min_visit.COLPROT, min_visit.ORIGPROT)
            if key_min_visit not in visits.keys():
                visits[key_min_visit] = image.Visit
            elif visits[key_min_visit] != image.Visit:
                print 'Multiple visits for one timepoint!'
                print subject
                print key_min_visit
                print visits[key_min_visit]
                print image.Visit

        return visits


def compute_t1_paths(source_dir, clinical_dir, dest_dir, subjs_list):
    """

    :param source_dir:
    :param clinical_dir:
    :param dest_dir:
    :param subjs_list:
    :return:
    """

    import pandas as pd
    from os import path, walk

    t1_col_df = ['Subject_ID', 'VISCODE', 'Visit', 'Sequence', 'Scan_Date',
                 'Study_ID', 'Field_Strength', 'Series_ID', 'Original']

    t1_df = pd.DataFrame(columns=t1_col_df)
    adni_merge_path = path.join(clinical_dir, 'ADNIMERGE.csv')
    # adni_screening_path = path.join(clinical_dir, 'ADNI_ScreeningList_8_22_12.csv')
    ida_meta_path = path.join(clinical_dir, 'IDA_MR_METADATA_Listing.csv')
    mprage_meta_path = path.join(clinical_dir, 'MPRAGEMETA.csv')
    mri_quality_path = path.join(clinical_dir, 'MRIQUALITY.csv')
    mayo_mri_qc_path = path.join(clinical_dir, 'MAYOADIRL_MRI_IMAGEQC_12_08_15.csv')

    adni_merge = pd.io.parsers.read_csv(adni_merge_path, sep=',')
    ida_meta = pd.io.parsers.read_csv(ida_meta_path, sep=',')
    mprage_meta = pd.io.parsers.read_csv(mprage_meta_path, sep=',')
    mri_quality = pd.io.parsers.read_csv(mri_quality_path, sep=',')
    mayo_mri_qc = pd.io.parsers.read_csv(mayo_mri_qc_path, sep=',')
    mayo_mri_qc = mayo_mri_qc[mayo_mri_qc.series_type == 'T1']


    for subj in subjs_list:
        adnimerge_subj = adni_merge[adni_merge.PTID == subj]
        # Sort the values by examination date
        adnimerge_subj = adnimerge_subj.sort_values('EXAMDATE')

        mprage_meta_subj = mprage_meta[mprage_meta.SubjectID == subj]
        mprage_meta_subj = mprage_meta_subj.sort_values('ScanDate')

        ida_meta_subj = ida_meta[ida_meta.Subject == subj]

        mri_quality_subj = mri_quality[mri_quality.RID == int(subj[-4:])]
        mayo_mri_qc_subj = mayo_mri_qc[mayo_mri_qc.RID == int(subj[-4:])]

        mprage_meta_subj_orig = mprage_meta_subj[mprage_meta_subj['Orig/Proc'] == 'Original']
        visits = visits_to_timepoints_t1(subj, mprage_meta_subj, adnimerge_subj)

        keys = visits.keys()
        keys.sort()
        for visit_info in visits.keys():
            if visit_info[1] == 'ADNI1':
                image_dict = adni1_image(subj, visit_info[0], visits[visit_info], mprage_meta_subj,
                                              ida_meta_subj, mri_quality_subj)
            elif visit_info[1] == 'ADNIGO':
                image_dict = adnigo_image(subj, visit_info[0], visits[visit_info], mprage_meta_subj,
                                               ida_meta_subj, mri_quality_subj, mayo_mri_qc_subj, visit_info[2])
            else:  # ADNI2
                image_dict = adni2_image(subj, visit_info[0], visits[visit_info], mprage_meta_subj_orig)

            if image_dict is None:
                image_dict = {'Subject_ID': subj,
                              'VISCODE': visit_info[0],
                              'Visit': visits[visit_info],
                              'Sequence': '',
                              'Scan_Date': '',
                              'Study_ID': '',
                              'Series_ID': '',
                              'Field_Strength': '',
                              'Original': True}

            row_to_append = pd.DataFrame(image_dict, index=['i', ])
            t1_df = t1_df.append(row_to_append, ignore_index=True)

    images = t1_df
    is_dicom = []
    nifti_paths = []
    count = 0

    for row in images.iterrows():

        image = row[1]
        seq_path = path.join(source_dir, str(image.Subject_ID), image.Sequence)

        count += 1
        # print 'Processing Subject ' + str(image.Subject_ID) + ' - Session ' + image.VISCODE + ', ' + str(
        #     count) + ' / ' + str(total)

        series_path = ''
        for (dirpath, dirnames, filenames) in walk(seq_path):
            found = False
            for d in dirnames:
                if d == 'S' + str(image.Series_ID):
                    series_path = path.join(dirpath, d)
                    found = True
                    break
            if found:
                break

        nifti_path = series_path
        dicom = True

        for (dirpath, dirnames, filenames) in walk(series_path):
            for f in filenames:
                if f.endswith(".nii"):
                    dicom = False
                    nifti_path = path.join(dirpath, f)
                    break

        is_dicom.append(dicom)
        nifti_paths.append(nifti_path)

    images.loc[:, 'Is_Dicom'] = pd.Series(is_dicom, index=images.index)
    images.loc[:, 'Path'] = pd.Series(nifti_paths, index=images.index)

    # TODO NEVER DO THIS, with empty paths is how we find errors
    # Drop all the lines that have the Path section empty
    # images = images.drop(images[images.Path == ''].index)

    # Store the paths inside a file called conversion_info inside the input directory
    images.to_csv(path.join(dest_dir, 't1_paths.tsv'), sep='\t', index=False)

    return images


def t1_paths_to_bids(images, bids_dir, dcm2niix="dcm2niix", dcm2nii="dcm2nii"):

    from adni_utils import center_nifti_origin, viscode_to_session
    from os import path, makedirs, system, remove
    from numpy import nan

    count = 0
    total = images.shape[0]

    for row in images.iterrows():
        image = row[1]
        subject = image.Subject_ID

        if image.Path is nan:
            print 'No path specified for ' + image.Subject_ID + ' in session ' + image.VISCODE
            continue

        count += 1
        print 'Processing subject ' + str(subject) + ' - session ' + image.VISCODE + ', ' + str(count) + ' / ' + str(total)

        session = viscode_to_session(image.VISCODE)
        image_path = image.Path
        bids_subj = subject.replace('_', '')
        output_path = path.join(bids_dir, 'sub-ADNI' + bids_subj, 'ses-' + session, 'anat')
        output_filename = 'sub-ADNI' + bids_subj + '_ses-' + session + '_T1w'

        try:
            makedirs(output_path)
        except OSError:
            if not path.isdir(output_path):
                raise

        if image.Is_Dicom:
            command = dcm2niix + ' -b n -z n -o ' + output_path + ' -f ' + output_filename + ' ' + image_path
            system(command)
            nifti_file = path.join(output_path, output_filename + '.nii')
            output_image = nifti_file + '.gz'

            # Check if conversion worked (output file exists?)
            if not path.isfile(nifti_file):
                command = dcm2nii + ' -a n -d n -e n -i y -g n -p n -m n -r n -x n -o ' + output_path + ' ' + image_path
                system(command)
                nifti_file = path.join(output_path, subject.replace('_', '') + '.nii')
                output_image = path.join(output_path, output_filename + '.nii.gz')

                if not path.isfile(nifti_file):
                    print 'DICOM to NIFTI conversion error for ' + image_path
                    continue

            center_nifti_origin(nifti_file, output_image)
            remove(nifti_file)

        else:
            output_image = path.join(output_path, output_filename + '.nii.gz')
            center_nifti_origin(image_path, output_image)
