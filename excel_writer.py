import os
import pandas as pd
import openpyxl as opxl

def GenerateDataFrame( all_paths_data, start, end ):
    max_num_paths = max( len( site_data.all_paths ) for site_data in all_sites_data.values() )
    # print( max_num_paths )

    col_names = [ f'{start}.{end}.DIST.{i}' for i in range( 1, max_num_paths+1 ) ]

    path_distances = []
    for site_data in all_sites_data.values():
        # print( site_data )
        path_distances.append( [ path_data.etch_len for path_data in site_data.all_paths ] )
    
    # col_names.append( 'SITE' )
    

    df = pd.DataFrame( path_distances, index=list( range(1,126+1) ), columns=col_names )

    # set the SITE col last to make sure it's the last col
    df[ 'SITE' ] = df.index.tolist()
    return df

def WriteDataFrameToXLSX( df, xl_filename ):
    output_file_folder = 'Board_Data'
    if not os.path.exists( output_file_folder ):
        os.makedirs( output_file_folder )
    output_file_path = f'{output_file_folder}/{xl_filename}'

    writer = pd.ExcelWriter( output_file_path, engine = 'openpyxl' )
    df.to_excel( excel_writer=writer, sheet_name='Path Data', index=False )
    writer.save()
    writer.close()