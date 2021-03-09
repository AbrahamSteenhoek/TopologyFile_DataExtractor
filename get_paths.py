import os
import re
from collections import defaultdict
from collections import namedtuple
import pandas as pd

import tops_nodal_graph as tng
import lookup_topo as lt
import input_parser as ip
import excel_writer as ew

# data about all the paths from start to end in a given site: start, end, all possible paths
# a Site is defined as one area on the PCB that is repeated across the PCB many times, like a set of testing probes, a set of memory chips, a set of power supplies, etc.
SiteData = namedtuple( 'SiteData', 'site topology_file start_node end_node all_paths' )

# data about one unique path: node path and dist 
PathData = namedtuple( 'PathData', 'path_num node_path etch_len' )

def GetSiteInfo( filename: str ):
    filename_extract = re.search( r'xnet_([^_]+)_([0-9]+).top$', filename )
    net_name = filename_extract.group( 1 )
    site_num = int( filename_extract.group( 2 ) )
    return net_name, site_num

def AddSiteSuffix( node_name, site_num ):
    return node_name if 'PR' in node_name else f'{node_name}_S{site_num}'

def PrintValidPaths( site_data ):
    # lt.SetTopologyFile( top_file=site_data.topology_file )
    site_num = site_data.site
    print( f'Site {site_num}: Found {len( site_data.all_paths )} paths from {site_data.start_node}_S{site_num} to {site_data.end_node}_S{site_num}')

    for i, path_data in enumerate( site_data.all_paths, start = 1 ):
        path = path_data.node_path
        path_str = ', '.join( tng.GetPathRefDes( path_data.node_path, site_data.topology_file ) )
        print( f'path# {i}: [ {path_str} ]' )
        print( f'\tlength of path# {i}: {tng.PathLength( path )} (MILs)')
    print()

# sort the list of topology files by the integer at the end of the filename instead of standard string ordering
def atoi( text ):
    return int( text ) if text.isdigit() else text
def numeric_keys( text ):
    return [ atoi(t) for t in re.split('(\d+)', text) ]

def main():
    target_net, start, end = ip.ParseInputArgs()
    if start in tng.DNIList():
        print( f'Start Node: {start} is labeled DNI in the schematic. Choose components that are not DNI.')
        quit()
    if end in tng.DNIList():
        print( f'End Node: {end} is labeled DNI in the schematic. Choose components that are not DNI.')
        quit()

    topo_dir = '.\\tops'
    try:
        os.chdir( topo_dir )
    except FileNotFoundError:
        print(f'The directory "{topo_dir}" cannot be found. Quitting...')
        quit()

    # topology file path
    topo_file_to_parse = target_net

    lt.SetTopologyFile( top_file=topo_file_to_parse )

    # transform topology file into nodal graph
    edge_list = tng.GetAdjList( topo_file=topo_file_to_parse )

    net_name, site_num = GetSiteInfo( topo_file_to_parse )

    # _ORIGIN suffix is needed to for the implementation of this nodal graph
    start_node = '{0}_ORIGIN'.format( tng.RefDesToNode( start ) )
    end_node = '{0}_ORIGIN'.format( tng.RefDesToNode( end ) )

    # print( f'Analyzing Net: {target_net}, Site: {site_num}')
    tng.FindAllPaths( edge_list, start_node, end_node )
    # this implementation creates duplicate or redundant paths that need to be trimmed
    valid_paths = tng.GetValidPaths( all_paths=tng.ConnectionPaths(), start_node=start_node, end_node=end_node )
    valid_paths = tng.RemoveLRNodes( nodal_paths=valid_paths )
    valid_paths = tng.RemoveDNIPaths( nodal_paths=valid_paths )

    # Create a data object for every valid path from start_node to end_node
    all_paths_list_temp = []
    for i, path in enumerate(  valid_paths , start = 1 ):
        all_paths_list_temp.append( PathData( i, path, tng.PathLength( path ) ) )
    # Store data from all paths into a Site data object
    AllPaths = SiteData( 1, topo_file_to_parse, start, end, all_paths_list_temp )

    AllPaths_df = ew.GenerateDataFrame( all_paths_data=AllPaths, start=start, end=end )
    print( 'Writing path data to Excel...' )
    os.chdir('..')
    ew.WriteDataFrameToXLSX( AllPaths_df, f'{start}-{end}-path-data.xlsx' )
    print( 'done!' )

if __name__ == "__main__":
    main()