
import os
from datetime import datetime as date
import time
import warnings # suppress warnings
warnings.filterwarnings("ignore")

## 3rd-party modules
import pandas as pd
import numpy as np
import math

from GAR import wb
from GAR.globals import read_parameters_global, read_partition_groups, show_message, add_logsheet
from .plot_quantfit import coeff_plot
from .condqgreg import condquant

###############################################################################
#%% Functions for step 2: quantfit
###############################################################################
def do_quantfit(debug=False):
    '''
    Entry point function called when button for quantile fits is called.

    This function cannot take in any arguments and can not have
    any return values due to limitation of the RunPython VBA code
    in xlwings.
    '''

    # Start measurement of time
    t0 = time.time()
    
    # Make sure a wb exists
    if wb is None:
        print('quantfit_main: wb is None')
        print('This may be due to not calling set_mock_caller_file')
        print('and setting the caller Workbook')
        import sys
        sys.exit(-1)
    
    if debug:
        print('+' * 40)
        print('start of do_quantfit')
        print('+' * 40)

    # Call prerun
    if debug:
        print('---- calling prerun_quantfit')
    dict_input_quantfit, df_quantfit = prerun_quantfit(debug=debug)

    if debug:
        print('dict_input_quantfit:')
        for key in dict_input_quantfit:
            print(key.ljust(20) + ':' + str(dict_input_quantfit[key]))
        print('df_quantfit:')
        print(df_quantfit)
        
    # Call main run
    if debug:
        print('---- calling run_quantfit')
    dict_output_quantfit = run_quantfit(dict_input_quantfit, df_quantfit, debug=debug)

    # Call postrun
    if debug:
        print('---- calling postrun_quantfit')
    postrun_quantfit(dict_output_quantfit, debug=debug)

    # End measurement of time
    t1 = time.time()

    # Total time for this operation (formatted string)
    tdiff = "{:.1f}".format(t1 - t0)
    
    sheets = [dict_output_quantfit[key] for key in dict_output_quantfit if key.find('sheet') != -1]
    message = 'Finished with quantfit in ' + tdiff + ' sec,\n'
    message += 'output is in sheets ' + ', '.join(sheets) 
    show_message(message,msgtype='info')
    
def prerun_quantfit(debug=False):
    '''
    Prerun function for step 2, quantfit.
    
    This function cannot take in any arguments due to limitations
    of the RunPython VBA code in xlwings.

    Check that the necessary steps beforehand have been done.
    Read in/check the input parameters and return a
    dict for input parameters and a df for data.
    '''

    if debug:
        print('=' * 30)
        print('start of prerun_quantfit')
        print('=' * 30)

    # Keys for input parameter dict
    keys = ['quantlist', 'regressors', 'sheet_input', 'sheet_quantreg', 'sheet_cond_quant']
    # Check that the necessary steps beforehand have been done.
    
    # --------------------------
    # Read in parameters
    # --------------------------
    dict_input_quantfit = read_parameters_quantfit()

    # --------------------------
    # Check parameter values
    # --------------------------
    check_parameters_quantfit(dict_input_quantfit, keys)

    # Read in global parameters
    # (this also checks if values have changed since being initially set)
    dict_global_params = read_parameters_global()

    # Add each key, val from dict_global_params to dict_input_quantfit
    for key, val in dict_global_params.items():
        # Check that the keys do not clash
        if key in dict_input_quantfit:
            message = 'dict_input_quantfit should not have key ' + key + ' that is common with dict_global_params'
            show_message(message, halt=True)
        dict_input_quantfit[key] = val

                        
    # Create df for data
    input_sheetname = dict_input_quantfit['sheet_input']
    df_quantfit = read_data_quantfit(input_sheetname)

    # return a dict for input parameters and a df
    return dict_input_quantfit, df_quantfit

def read_parameters_quantfit():
    '''
    Read in parameters for quantfit.

    The cell positions for inputs are hardcoded in.
    Parameter value and range checking is done in the check_parameters_quantfit function.
    '''

    # Create dict for parameters
    dict_parameters_quantfit = dict()

    # ---------------------------#
    # Read in necessary values
    # ---------------------------#

    # Read in quantlist
    cellpos = 'F31'
    # Get a list of all values starting at cellpos going down
    dict_parameters_quantfit['quantlist'] = wb.sheets['Input_parameters'].range(cellpos).expand('down').value

    # Read in info on regressors.
    dict_parameters_quantfit['regressors'] = dict()
    # Start with the first cell that contains the regressors.
    startrow = 31
    cellpos = 'A' + str(startrow)
    # Read down and get a list of all regressors
    regressors = wb.sheets['Input_parameters'].range(cellpos).expand('down').value
    if not isinstance(regressors, (list, tuple)):
        regressors = [regressors]
    for iregressor, regressor in enumerate(regressors):
       

        # Get the cells for transformation and optional parameter
        # from columns B and C for this row
        colnum = startrow+iregressor
        transform = wb.sheets['Input_parameters'].range('B' + str(colnum)).value
        option    = wb.sheets['Input_parameters'].range('D' + str(colnum)).value
        dict_parameters_quantfit['regressors'][regressor+'_trans_'+str(iregressor)+'_'+transform] = dict()
        # Set as values of dict
        dict_parameters_quantfit['regressors'][regressor+'_trans_'+str(iregressor)+'_'+transform]['transform'] = transform
        dict_parameters_quantfit['regressors'][regressor+'_trans_'+str(iregressor)+'_'+transform]['option'] = option

    # Read in output sheets
    startrow = 51
    for isheetname, sheetname in enumerate(['sheet_quantreg', 'sheet_cond_quant']):
        colnum = startrow + isheetname
        cellpos = 'B' + str(colnum)
        dict_parameters_quantfit[sheetname] = wb.sheets['Input_parameters'].range(cellpos).value
        # checking of values will be done in check_parameters_quantfit

    # The sheetname for the input is read in from what is in cell B24.
    # This is read in for do_partition() but since there is no way to connect
    # the output, we have to assume that the user has not changed this cell
    # since running the partitions.
    cellpos = 'B24'
    dict_parameters_quantfit['sheet_input'] = wb.sheets['Input_parameters'].range(cellpos).value

    return dict_parameters_quantfit

def check_parameters_quantfit(dict_input_quantfit, keys):
    '''
    Check the input parameters for quantfit.
    '''

    # Check that all keys exist
    for key in keys:
        if key not in dict_input_quantfit:
            message = 'key ' + key + ' not found in dict_input_quantfit'
            show_message(message)

    input_sheets = ['Readme', 'Input_parameters', 'Partition_groups', 'Data', 'Processing_Log']
    for key in keys:
        val = dict_input_quantfit[key]

        if key == 'quantlist':
            # Check that all values are between 0 and 1,
            # and that the necessary values of 0.10, 0.25, 0.50, 0.75, 0.90 exist
            vals_np = np.array(val) # create np.array for value checking
            if not (np.all(0 < vals_np) and np.all(vals_np < 1)):
                message = 'All values of quantlist must be between 0 and 1'
                message+= 'Given values: ' + str(val)
                show_message(message, halt=True)
            # Check that necessary values are present
            necessary_vals = [0.10, 0.25, 0.50, 0.75, 0.90]
            for _val in necessary_vals:
                if _val not in val:
                    message = 'Value of ' + str(_val) + ' must be included in quantlist'
                    message += 'Given values: ' + str(val)
                    show_message(message, halt=True)

        if key == 'regressors':
            # val is a dict of dicts with keys [regressor]['transform/option']
            for regressor in val:
                transform = val[regressor]['transform']
                option    = val[regressor]['option']

                # Check that transform is a valid value from the pulldown menu
                if transform not in ['None', 'Lagged', 'MVA','Power','Diff','ChangeRate']:
                    message = 'transform for ' + regressor + ' was not a valid option, given ' + transform
                    show_message(message, halt=True)

                # If 'No transformation' or 'Log' was chosen, make sure no option was given
                if transform in ['None']:
                    if option is not None:
                        message = 'option for regressor = ' + regressor + ' with transform of ' + transform + ' must not have option set'
                        show_message(message, halt=True)
                    
                # If 'Lagged' or 'Moving Average' was chosen, make sure lag exists and is an int
                if transform in ['Lagged', 'MVA','Power','Diff','ChangeRate']:
                    if type(option) != float or abs(int(option) - option) > 1E-5:
                        message = 'option for regressor = ' + regressor + ' with transform of ' + transform + ' must have option of int, given ' + str(option)
                        show_message(message, halt=True)
                    # Since the value is less than 1E-5 away from an int,
                    # convert to int so that there are no problems later
                    dict_input_quantfit['regressors'][regressor]['option'] = int(option)
        
        if key == 'sheet_input':
            # If nothing had been specified in the cell containing the partition output sheet,
            # set to default
            if val is None:
                sheetname = 'Output_partitions'
                dict_input_quantfit[key] = sheetname

                # Get existing sheetnames
                sheetnames = [sheet.name for sheet in wb.sheets]
                if sheetname not in sheetnames:
                    message = 'Input sheet for quantfit: ' + sheetname + ' does not exist'
                    show_message(message, halt=True)

        elif key.find('sheet_') != -1:
            # If a value was specified, check that it is not one of the
            # input sheet names and use it as the output sheet name.
            # Otherwise we will use the default 'Output_quantfits'
            if val is None:
                if key == 'sheet_quantreg':
                    dict_input_quantfit[key] = 'Quant reg coefficients'
                elif key == 'sheet_cond_quant':
                    dict_input_quantfit[key] = 'Conditional quantiles'
                else:
                    message = 'No sheet called ' + key + ' should exist'
                    show_message(message, halt=True)
            else:
                # Check that the specified sheetname is not one of the inputs
                # (it is OK that it is the same name as an existing sheet if
                # that sheet is an output)
                if val in input_sheets:
                    message = key + ' specified as ' + val + ', cannot be the same as necessary input sheet'
                    show_message(message, halt=True)
                    
def read_data_quantfit(sheetname):
    '''
    Read in the input data for quantfit.
    Checks for the sheetname should have been done in check_parameters_quantfit.
    '''
    dall = wb.sheets[sheetname].range('A1').options(pd.DataFrame,index=False,expand='table').value
    return dall

def run_quantfit(dict_input_quantfit, df_quantfit, debug=False):
    '''
    Main run function for step 2, quantfit.

    Takes in as arguments a dict for input parameters
    and a df for data. Outputs a dict for output parameters.

    Does quantile fits and returns a dict of output parameters.
    ** This function should be independent of any Excel input/output
    and be executable as a regular Python function independent of Excel. **
    '''
    
    warnings.filterwarnings("ignore")

    if debug:
        print('=' * 30)
        print('start of run_quantfit')
        print('=' * 30)

    # ------------------------
    # Create DataFrame for log
    # ------------------------
    log_frame = pd.DataFrame(columns=['Time','Action'])

    # ------------------------
    # Create output dict
    # ------------------------
    dict_output_quantfit = dict()
      
    # ------------------------
    # Copy the output sheet names
    # from dict_input_quantfit
    # ------------------------
    for key in dict_input_quantfit:
        if key.find('sheet_') != -1:
            dict_output_quantfit[key] = dict_input_quantfit[key]
    
    # ------------------------
    # Get parameters from
    # dict_input_quantfit
    # ------------------------
    horizon = dict_input_quantfit['horizon']
    depvar  = dict_input_quantfit['target'] + '_hz_' + str(horizon)

    # Get the list of regressors from the sheet Partition_groups
    #dict_groups = read_partition_groups() obsoleted
    
    #regressors = list(dict_groups.keys())
    #print(dict_input_quantfit['regressors'].keys())
    regressors=list(dict_input_quantfit['regressors'].keys())
    dict_output_quantfit['regressors']=dict_input_quantfit['regressors']
    
    df_quantfit = df_quantfit.set_index(df_quantfit['date'], drop=False) 
    for reg_long in  regressors:
        reg_short=reg_long.split('_trans_')[0]
        if dict_input_quantfit['regressors'][reg_long]['transform']=='None':
            df_quantfit[reg_long]=df_quantfit[reg_short]
        elif dict_input_quantfit['regressors'][reg_long]['transform']=='Lagged':
            df_quantfit[reg_long]=df_quantfit[reg_short].shift(dict_input_quantfit['regressors'][reg_long]['option'])
        elif dict_input_quantfit['regressors'][reg_long]['transform']=='MVA':
            df_quantfit[reg_long]=df_quantfit[reg_short].rolling(window=dict_input_quantfit['regressors'][reg_long]['option']).mean()
        elif dict_input_quantfit['regressors'][reg_long]['transform']=='Power': 
            df_quantfit[reg_long]=df_quantfit[reg_short]**(dict_input_quantfit['regressors'][reg_long]['option'])
        elif dict_input_quantfit['regressors'][reg_long]['transform']=='Diff': 
            df_quantfit[reg_long]=df_quantfit[reg_short].diff(dict_input_quantfit['regressors'][reg_long]['option'])
        elif dict_input_quantfit['regressors'][reg_long]['transform']=='ChangeRate': 
            df_quantfit[reg_long]=df_quantfit[reg_short].pct_change(dict_input_quantfit['regressors'][reg_long]['option'])

    print(df_quantfit.iloc[-1])        
    #df_quantfit = df_quantfit[:-horizon]
    # ------------------------
    # Run the quantfit
    # ------------------------
    qcoeff_all, dcond_quantiles_all, loco_all, exitcode = condquant(df_quantfit, depvar, regressors, horizon,dict_input_quantfit['quantlist'])
    print(qcoeff_all[qcoeff_all['quantile']==0.1])
    if exitcode<1:
        action = 'Failed to do quantile regression, exit code: ' + str(exitcode)
    else:
        action = 'Quantile regression finished succesfully.'
    tn = date.now().strftime('%Y-%m-%d %H:%M:%S')
    log = pd.Series({'Time': tn, 'Action': action})
    log_frame.append(log, ignore_index=True)

    # Add return values
    figs={}
    
    figs=coeff_plot(qcoeff_all,regressors,dict_input_quantfit['quantlist'])
    dict_output_quantfit['qcoef']      = qcoeff_all
    dict_output_quantfit['cond_quant'] = dcond_quantiles_all
    dict_output_quantfit['localprj']    = loco_all
    dict_output_quantfit['figs'] = figs
    
    return dict_output_quantfit
    
def postrun_quantfit(dict_output_quantfit, debug=False):
    '''
    Postrun function for step 2, quantfit.

    Takes as input dict from main run function.

    This function cannot return any values due to limitations
    of the RunPython VBA code in xlwings.
    
    '''

    if debug:
        print('=' * 30)
        print('start of postrun_quantfit')
        print('=' * 30)

    # Create DataFrame for log
    log_frame = pd.DataFrame(columns=['Time','Action'])
    
    # Create the output sheets
    sheetvars = [key for key in dict_output_quantfit if key.find('sheet') != -1]
    for sheetvar in sheetvars:

        # Don't do anything for the input sheet
        if sheetvar == 'sheet_input':
            continue
        
        # Check that sheetvar exists as a key in dict_output_quantfit
        if sheetvar not in dict_output_quantfit:
            message = 'sheetvar ' + sheetvar + ' is not a key for dict_output_quantfit'
            show_message(message, halt=True)

        # Get the actual sheet name
        sheetname = dict_output_quantfit[sheetvar]

        # Get existing sheetnames
        sheetnames = [sheet.name for sheet in wb.sheets]

        try:
            # Clear the sheet if it already exists
            if sheetname in sheetnames:
                wb.sheets[sheetname].clear()
                action = 'Cleared sheet ' + sheetname
            # Otherwise add it after the "Data" sheet
            else:
                wb.sheets.add(sheetname, after='Data')
                # Set output sheet colors to blue
                wb.sheets[sheetname].api.Tab.ColorIndex = 23
                action = 'Created sheet ' + sheetname
        except:
            action = 'Unable to access sheet ' + sheetname

        # Add to log
        tn=date.now().strftime('%Y-%m-%d %H:%M:%S')
        log = pd.Series({'Time': tn, 'Action': action})
        log_frame = log_frame.append(log, ignore_index=True)
        
    # end of loop over output sheetvars

    # Write out quantfit results
    try:
        for sheetvar in sheetvars:
            sheetname = dict_output_quantfit[sheetvar]
            if sheetvar == 'sheet_quantreg':
                wb.sheets[sheetname].range('A1').options(index=False).value = dict_output_quantfit['qcoef']
                wb.sheets[sheetname].autofit()
            elif sheetvar == 'sheet_cond_quant':
                wb.sheets[sheetname].range('A1').options(index=True).value = dict_output_quantfit['cond_quant']
                wb.sheets[sheetname].autofit()
        action='Quantfit results saved succesfully.'
    except:
        action='Unable to output quantfit results.'
        print(action)
        
    sheetname = dict_output_quantfit['sheet_quantreg']    
    try:
        wb.sheets[sheetname].pictures[0].delete()
    except:
        pass
    sheet = wb.sheets[sheetname]
    fig = dict_output_quantfit['figs']

    # Set the path of the output file to be in the same dir as the
    # calling Excel file
    fullpath = os.path.abspath(os.path.dirname(wb.fullname) + '/figures')
    if not os.path.isdir(fullpath):
        os.makedirs(fullpath)
    outfilename = fullpath+'\\quantfit_'+date.now().strftime('%Y_%m-%d@%H_%M-%S')+'.png'
    fig.savefig(outfilename)
    cr=len(dict_output_quantfit['regressors'].keys())
    try:
        pic=sheet.pictures.add(fig, name='MyPlot_q', update=True, left=sheet.range('N6').left, top=sheet.range('N6').top, height=340*(cr//4+1), width=240*(min(4,cr+1)))
        pic.height=340*(cr//4+1)
        pic.width=240*(min(4,cr+1))
        
        action = 'Quantile figure saved'
    except:
        action = 'Unable to add figure to sheet ' + sheetname
        
    # Add to log
    tn=date.now().strftime('%Y-%m-%d %H:%M:%S')
    log = pd.Series({'Time': tn, 'Action': action})
    log_frame = log_frame.append(log, ignore_index=True)

    # Write out log_frame
    add_logsheet(wb, log_frame, colnum=3)
