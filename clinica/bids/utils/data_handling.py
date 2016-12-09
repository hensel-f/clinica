from os import path
from glob import glob
import pandas as pd
import os
from ..converter_utils import MissingModsTracker, print_statistics

__author__ = "Sabrina Fontanella"
__copyright__ = "Copyright 2016, The Aramis Lab Team"
__credits__ = ["Sabrina Fontanella"]
__license__ = ""
__version__ = "1.0.0"
__maintainer__ = "Sabrina Fontanella"
__email__ = "sabrina.fontanella@icm-institute.org"
__status__ = "Development"


def create_merge_file(bids_dir, out_dir):
    """
     Merge all the TSV files containing clinical data of BIDS compliant dataset

     Args:
        bids_directory: path of the dataset
        out_directory: output path

    """
    col_list = []
    scans_dict = {}

    if not os.path.isfile(path.join(bids_dir, 'participants.tsv')):
        raise 'participants.tsv not found'
    participants_df = pd.read_csv(path.join(bids_dir, 'participants.tsv'), sep='\t')
    subjs_paths = glob(path.join(bids_dir, '*sub-*'))

    out_file_name = out_dir.split(os.sep)[-1]
    if len(out_file_name) == 0 or out_dir == '.':
        out_file_name = 'merge_tsv.tsv'
    else:
        # Extract the path of the file
        out_dir = os.path.dirname(out_dir)

    if '.' not in out_file_name:
        out_file_name = out_file_name + '.tsv'
    else:
        extension = os.path.splitext(out_file_name)[1]
        if extension != '.tsv':
            raise 'Output file must be .tsv.'

    if out_dir == '.':
        out_dir = os.getcwd()

    for col in participants_df.columns.values:
        col_list.append(col)

    merged_df = pd.DataFrame(columns=col_list)

    for sub_path in subjs_paths:
        sub_name = sub_path.split(os.sep)[-1]
        # For each subject, extract the relative row from the dataframe
        row_participant = participants_df[participants_df['participant_id'] == sub_name]
        # Open the sessions file related to the subject
        sessions_df = pd.read_csv(path.join(sub_path, sub_name+'_sessions.tsv'), sep='\t')

        # For each session found extract the information contained in the scans files
        for line in range(0, len(sessions_df)):
            # Extract and convert to a dictonary information regarding the session
            row_sessions = sessions_df.iloc[line]
            row_session_df = pd.DataFrame([row_sessions])
            new_cols = [s for s in row_session_df.columns.values if s not in col_list]
            if len(new_cols)!=0:
                for i in range(0, len(new_cols)):
                    col_list.append(new_cols[i])

            session_id = row_sessions['session_id']
            if os.path.isfile(path.join(bids_dir, sub_name, 'ses-'+session_id, sub_name+'_'+'ses-'+session_id+'_scans.tsv')):
                scans_df = pd.read_csv(path.join(bids_dir, sub_name, 'ses-'+session_id, sub_name+'_'+'ses-'+session_id+'_scans.tsv'), sep='\t')
                for i in range(0, len(scans_df)):
                    for col in scans_df.columns.values:
                        if col == 'filename':
                            pass
                        else:
                            file_scan = scans_df.iloc[i]['filename']
                            file_name = file_scan.split('/')[1]
                            # Remove the extension .nii.gz
                            file_name = os.path.splitext(os.path.splitext(file_name)[0])[0]
                            file_parts = file_name.split('_')
                            last_pattern_index = len(file_parts) - 1
                            mod_type = file_parts[last_pattern_index]
                            value = scans_df.iloc[i][col]
                            new_col_name = col+'_'+mod_type
                            scans_dict.update({new_col_name:value})
                row_scans = pd.DataFrame(scans_dict, index=[0])
            else:
                row_scans = pd.DataFrame()

            new_cols = [s for s in row_scans.columns.values if s not in col_list]
            if len(new_cols)!=0:
                for i in range(0, len(new_cols)):
                    col_list.append(new_cols[i])

            row_to_append_df= pd.DataFrame(columns=row_participant.columns)
            for col in row_participant:
                row_to_append_df[col] = row_participant[col]

            # Append all the data inside session_df
            for col in row_session_df:
                row_to_append_df[col] = row_session_df[col].values[0]

            for col in row_scans:
                row_to_append_df[col] = row_scans[col].values[0]

            merged_df = merged_df.append(row_to_append_df)
        scans_dict = {}

    merged_df = merged_df[col_list]
    merged_df.to_csv(path.join(out_dir, out_file_name), sep='\t', index=False)


def find_mods_and_sess(dataset_dir):
    '''
    Finds all the modalities available for a given dataset

    Args:
        dataset_dir: bids input path
    '''
    mods_dict = {}
    mods_list = []
    mods_aval = []
    subjects_paths_lists = glob(path.join(dataset_dir, '*sub-*'))
    for sub_path in subjects_paths_lists:
        ses_paths = glob(path.join(sub_path, '*ses-*'))
        for session in ses_paths:
            ses_name = session.split(os.sep)[-1]
            mods_aval = []
            if mods_dict.has_key('sessions'):
                if not ses_name in mods_dict['sessions']:
                    mods_dict['sessions'].append(ses_name)
            else:
                mods_dict.update({'sessions':[ses_name]})
            mods_paths_folders = glob(path.join(session, '*/'))

            for p in mods_paths_folders:
                p = p[:-1]
                mods_aval.append(p.split('/').pop())

            if 'func' in mods_aval:
                list_funcs_paths = glob(path.join(session, 'func', '*bold.nii.gz'))
                for func_path in list_funcs_paths:
                    func_name = func_path.split(os.sep)[-1]
                    func_name_tokens = func_name.split('_')
                    func_task = func_name_tokens[2]
                if mods_dict.has_key('func'):
                    if not 'func_'+func_task in mods_dict['func']:
                        mods_dict['func'].append('func_'+func_task)
                else:
                    mods_dict.update({'func': ['func_'+func_task]})

                if not 'func_'+func_task in mods_list:
                    mods_list.append('func_'+func_task)

            if 'dwi' in mods_aval:
                if not mods_dict.has_key('dwi'):
                    mods_dict.update({'dwi': ['dwi']})
                if not 'dwi' in mods_list:
                    mods_list.append('dwi')

            if 'anat' in mods_aval:
                anat_files_paths = glob(path.join(session, 'anat', '*'))

                for anat_file in anat_files_paths:
                    anat_name = anat_file.split(os.sep)[-1]

                    # Extract the name of the file without the extension
                    if '.nii.gz' in anat_name:
                        anat_name = anat_name.replace('.nii.gz', '')
                        anat_ext = 'nii.gz'
                    else:
                        anat_name = os.path.splitext(anat_name.split(os.sep)[-1])[0]
                        anat_ext = os.path.splitext(anat_name.split(os.sep)[-1])[1]

                    if anat_ext != 'json':
                        file_parts = anat_name.split("_")
                        anat_type = file_parts[len(file_parts) - 1]

                        if mods_dict.has_key('anat'):
                            if anat_type not in mods_dict['anat']:
                                anat_aval = mods_dict['anat']
                                anat_aval.append(anat_type)
                                mods_dict.update({'anat': anat_aval})
                        else:
                            mods_dict.update({'anat': [anat_type]})

                        if anat_type not in mods_list:
                            mods_list.append(anat_type)
    return mods_dict


def compute_missing_mods(in_dir, out_dir):

    # Find all the modalities and sessions available for the input dataset
    summary_file = open(path.join(out_dir, 'missing_mods_sess_summary.txt'), 'w')
    mods_and_sess= find_mods_and_sess(in_dir)
    sessions_found = mods_and_sess['sessions']
    mods_and_sess.pop('sessions')
    mods_avail_dict = mods_and_sess
    mods_avail = [j for i in mods_avail_dict.values() for j in i]
    cols_dataframe = mods_avail[:]
    cols_dataframe.insert(0, 'participant_id')
    mmt = MissingModsTracker(sessions_found, mods_avail)
    out_file_name = out_dir.split(os.sep)[-1]
    if len(out_file_name) == 0 or out_dir == '.':
        out_file_name = 'missing_mods_'
    else:
        # Extract the path of the file
        out_dir = os.path.dirname(out_dir)

    if out_dir == '.':
        out_dir = os.getcwd()

    missing_mods_df = pd.DataFrame(columns=cols_dataframe)
    row_to_append_df = pd.DataFrame(columns=cols_dataframe)
    subjects_paths_lists = glob(path.join(in_dir, '*sub-*'))

    if len(subjects_paths_lists) == 0:
        raise "No subjects found or dataset not BIDS complaint."
    # Check the modalities available for each session
    for ses in sessions_found:
        mods_avail_bids = []
        for sub_path in subjects_paths_lists:
            subj_id = sub_path.split(os.sep)[-1]
            row_to_append_df['participant_id'] = pd.Series(subj_id)
            ses_path_avail = glob(path.join(sub_path, ses))
            if len(ses_path_avail)==0:
                mmt.increase_missing_ses(ses)
                for mod in mods_avail:
                    row_to_append_df[mod] = pd.Series('-')
            else:
                ses_path = ses_path_avail[0]
                mods_paths_folders = glob(path.join(ses_path, '*/'))

                for p in mods_paths_folders:
                    p = p[:-1]
                    mods_avail_bids.append(p.split('/').pop())


                # Check if each modalities is available or missing
                if 'func' in mods_avail_bids:
                    # Extract all the task available
                    for m in mods_avail_dict['func']:
                        tokens = m.split('_')
                        task_name = tokens[1]
                        task_avaL_list = glob(path.join(ses_path,'func' ,'*'+task_name+'*'))

                        if len(task_avaL_list) == 0:
                            row_to_append_df[m] = pd.Series('0')
                        else:
                            row_to_append_df[m] = pd.Series('1')
                else:
                    if 'func' in mods_avail:
                        for m in mods_avail_dict['func']:
                            row_to_append_df[m] = pd.Series('-')
                        mmt.add_missing_mod(ses, m)

                if ['dwi' in m for m in mods_paths_folders]:
                    row_to_append_df['dwi'] = pd.Series('1')
                else:
                    row_to_append_df['dwi'] = pd.Series('0')
                    mmt.add_missing_mod(ses, 'dwi')

                if ['anat' in m for m in mods_paths_folders]:
                    for m in mods_avail_dict['anat']:
                        anat_aval_list = glob(path.join(ses_path, 'anat', '*.nii.gz'))
                        if len(anat_aval_list) > 0:
                            row_to_append_df[m] = pd.Series('1')
                        else:
                            row_to_append_df[m] = pd.Series('0')
                            mmt.add_missing_mod(ses, m)

            missing_mods_df = missing_mods_df.append(row_to_append_df)
            row_to_append_df = pd.DataFrame(columns=cols_dataframe)

        missing_mods_df = missing_mods_df[cols_dataframe]
        missing_mods_df.to_csv(path.join(out_dir, out_file_name+ses+'.tsv'), sep='\t', index=False)
        missing_mods_df = pd.DataFrame(columns=cols_dataframe)

    print_statistics(summary_file, len(subjects_paths_lists), sessions_found, mmt)


def create_subs_sess_list(dataset_path, out_dir):
    file_name = out_dir.split(os.sep)[-1]
    if len(file_name) == 0 or out_dir=='.':
        file_name = 'subjects_sessions_list.tsv'
    else:
        # Extract the path of the file
        out_dir = os.path.dirname(out_dir)

    if '.' not in file_name:
        file_name = file_name+'.tsv'
    else:
        extension = os.path.splitext(file_name)[1]
        if extension != '.tsv':
            raise 'Output file must be .tsv.'

    if out_dir ==  '.':
        out_dir = os.getcwd()

    subjs_sess_tsv = open(path.join(out_dir, file_name), 'w')
    subjs_sess_tsv.write('participant_id' + '\t' + 'session_id' + '\n')

    subjects_paths = glob(path.join(dataset_path, '*sub-*'))
    if len(subjects_paths) == 0:
        raise 'Dataset empty or not BIDS-compliant.'
    for sub_path in subjects_paths:
        subj_id = sub_path.split(os.sep)[-1]
        sess_list = glob(path.join(sub_path, '*ses-*'))
        for ses_path in sess_list:
            session_name = ses_path.split(os.sep)[-1]
            subjs_sess_tsv.write(subj_id+'\t'+session_name+'\n')

    subjs_sess_tsv.close()




