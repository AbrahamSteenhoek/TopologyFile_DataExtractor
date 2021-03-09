import re
import os
from collections import defaultdict
from enum import Enum

from numpy.lib.function_base import append

import lookup_topo as lt

refDes_to_compID_map = {}

def DNIList():
    '''
    List of generic names for all components in the schematic
    '''
    dni_list_generic = [
        'NULL' # Fill this list with anything that is listed as DNI in the schematic
    ]

    return dni_list_generic.copy()

def RNS():
    '''
    Returns the unique suffix string that specifies a node as the root node
    Root Node Suffix (RNS)
    '''
    return '_ORIGIN'

def GetNodeRoot( node_name ):
    return node_name[:-7] if ( RNS() in node_name ) else node_name[:-2]

def RefDesToNode( refDes ):
    if refDes not in refDes_to_compID_map.keys():
        print( f'Error: node "{refDes}" is not in this topology file. Quitting...' )
        quit()
    else:
        return refDes_to_compID_map[ refDes ]

def AddEdge( edge_list, edges ):
    edge1 = edges[0]
    edge2 = edges[1]

    edge_list[edge1].append( edge2 )
    edge_list[edge2].append( edge1 )

def GetAdjList( topo_file ):
    '''
    Each topology file has a Nodes List, which shows the connections between all of the components in the topology file.
    
    ------------------------------------------------------------
    (Nodes
        ("node1"
            (terms "C1.1" "C2.1")
        )
        ("node2"
            (terms "C1.2" "C3.1")
        )
        ...
    )
    ------------------------------------------------------------
    
    The nodes in the topology file are abstract, and solely exist to show the connections between the components.,
        while the components (C1, C2, C3, etc.) are the edges

    Here in these two listings shown in the Nodes list, we see the following connections:
        * C1 is connected to C2 at node1
        * C1 is connected to C3 at node2
    
    The suffix integer C1(.1) at the end of each component in the Nodes listing tells which end of the component is connected at that node
        * For example, C1 is a resistor, with its right end connected to C2, and its left end connected to C3
            (no for-sure way to tell which number means right or left, just not the same side if the suffix integer is different)
        * Note that C2 is NOT connected to C3 (at least in the listings shown)
        * Components with suffix integers will be called LR Nodes (left/right nodes)
    
    In this approach, we turn the components into nodes, so that traversal is much easier.
    
    To do this, we make a traditional adjacency list, using each node listing as an edge (where the components are now nodes), and ignoring the abstract node names.
    
    Since each node in the Node listing has component names with a suffix integer, there is no root component node to connect all of the component nodes with suffix integers.
        * For example, conceptually we know that C1 is connected to C2 and C3, 
            but we don't have that information explicity in this Node listing from the topology file.
        * To fix this issue, we manually add a root node for C1 with a specially designated prefix: "_ORIGIN"
            ( C1_ORIGIN ) that is connected to both C1.1 and C1.2
        * This approach makes the appropriate node connections, while adding some redundant or unecessary node connections
            which need to be filtered out later when plotting all possible paths between two nodes.
    '''
    edges = defaultdict(list)

    # save the topology file currently set in the lookup_topo API in case it's different than the topology file passed in
    save_topo_file = lt.GetTopologyFile()
    lt.SetTopologyFile( topo_file )

    with open( topo_file , 'r' ) as top:
        while ( skipline := top.readline() ):
            # skip lines to nodal graph
            if 'Nodes' in skipline:
                while ')' not in ( top.readline() ): # ends with closing paren for nodes section
                    line_with_edges = top.readline()
                    edge = re.findall( r'\.([^"]+)', line_with_edges )

                    for node in edge:
                        node_root = GetNodeRoot( node )
                        refDes_to_compID_map[ lt.LookupRefDes( node_root ) ] = node_root 
                        # print( f'node name: {node} | refDes: {lt.LookupRefDes(topo_file, node[:-2] )}' )

                    # handle case in topology file when only one node is in the listing
                    if len( edge ) == 1:
                        edges[ edge[0] ]

                    if len( edge ) == 2:
                        AddEdge( edges, edge )

                    # TODO: write function to handle edges greater than 3
                    # break one edge with 3 nodes into 3 edges with 2
                    if len( edge ) == 3:
                        edge1 = [ edge[0], edge[1] ]
                        edge2 = [ edge[1], edge[2] ]
                        edge3 = [ edge[0], edge[2] ]
                        AddEdge( edge_list = edges, edges = edge1 )
                        AddEdge( edge_list = edges, edges = edge2 )
                        AddEdge( edge_list = edges, edges = edge3 )

                    # next line is closing paren for current node (skip it)
                    top.readline()
    
    component_suffix_int_count = defaultdict(int)

    # figure out how many different suffix integers there are for each component
    for node in edges.keys():
        component_root = GetNodeRoot( node )
        component_origin = f'{ component_root }{ RNS() }' # Using [:-2] to trim off the .# substring first

        component_suffix_int_count[ component_origin ] = component_suffix_int_count[ component_origin ] + 1

        # For all component nodes with suffix integers, add connection to _ORIGIN node 
        edges[node].append( component_origin )
    
    # Add connection from _ORIGIN node to all component nodes with suffix integers
    for component_origin in component_suffix_int_count.keys():
        edges[ component_origin ] = []
        for i in range( 1, component_suffix_int_count[component_origin] + 1 ): # +1 because python range() function is exclusive at the end
            component_root = GetNodeRoot( component_origin )
            edges[ component_origin ].append( f'{ component_root }.{ i }') # trim off '_ORIGIN' substring with [:-7]

    # restore topology file for lookup api in case it was a different one
    lt.SetTopologyFile( save_topo_file )

    return edges

def PrintAdjList( adj_list ):
    for key, val in adj_list.items():
        # print( f'{lt.LookupRefDes( tng.GetNodeRoot(key) )}: {[lt.LookupRefDes( tng.GetNodeRoot(x) ) for x in val]}' )
        print( f'{key}: {val}')

connectionPath = []
connectionPaths = []

def FindAllPaths( adj_list, start_node, dest_node ):
    '''
    Uses DFS to find all the paths between the starting node and ending node
    '''
    for next_node in adj_list[ start_node ]:
        if ( next_node == dest_node ):
            temp_path = []
            for n in connectionPath:
                temp_path.append( n )
            connectionPaths.append( temp_path )
        elif next_node not in connectionPath:
            connectionPath.append( next_node )
            FindAllPaths( adj_list, next_node, dest_node )
            connectionPath.pop()

def GetValidPaths( all_paths, start_node, end_node ):
    valid_paths = all_paths.copy()
    start_node_root = GetNodeRoot( start_node )
    end_node_root = GetNodeRoot( end_node )
    # forgive the redundancy. Removing invalid paths according to these criteria in order made it easier and more readable for me lol

    # Shouldn't have ORIGIN node for the starting or ending nodes in the path already
    #   Only the LR nodes for the starting and ending nodes should be in the path
    remaining_paths = valid_paths.copy()
    for path in all_paths:
        # print( f'inspecting path: {path}')
        if start_node in path or end_node in path:
            # print( 'found start node in path:')
            # print( path )
            # print( 'removing...')
            valid_paths.remove( path )

    # Remove paths that have a pass by the end node by the L/R node instead
    remaining_paths = valid_paths.copy()
    for path in remaining_paths:
        path_to_combined_string = '\t'.join( path )
        end_node_root = GetNodeRoot( end_node )
        if path_to_combined_string.count( end_node_root ) > 1:
            valid_paths.remove( path )

    # Remove nodes that have just one L/R node instead of passing through the ORIGIN of the component
    remaining_paths = valid_paths.copy()
    for path in remaining_paths:
        path_to_combined_string = '\t'.join( path )

        for node in path:
            node_root = GetNodeRoot( node )
            # print( f'inspecting node: {node}, with node root: {node_root}')
            if node_root not in [ start_node_root, end_node_root ] and path_to_combined_string.count( node_root ) < 3:
                valid_paths.remove( path )
                break


    return valid_paths

def RemoveLRNodes( nodal_paths ):
    '''
    Removes all of the components with suffix integers from the path and connects the origins together.
    '''
    consolidated_paths = []
    for path in nodal_paths:
        consolidated_path = []
        for node in path:
            node_root = GetNodeRoot( node )
            if node_root not in consolidated_path:
                consolidated_path.append( node_root )
        consolidated_paths.append( consolidated_path )

    return consolidated_paths

def RemoveDNIPaths( nodal_paths ):
    non_dni_paths = nodal_paths
    remaining_paths = non_dni_paths.copy()
    for path in remaining_paths:
        for node in path:
            node_refDes = lt.LookupRefDes( node )
            node_refDes_no_suffix = node_refDes.split('_')[0]
            if node_refDes_no_suffix in DNIList():
                # print( f'found invalid path with DNI: {node_refDes}')
                non_dni_paths.remove( path )
    
    return non_dni_paths

# Returns the sum of all trace segments in the path in MILs
def PathLength( path ):
    trace_len_sum = 0
    for node in path:
        if lt.LookupComponentType( node ) == 'Trace':
            trace_len_sum += lt.LookupTraceLength( node )
    return trace_len_sum

def GetPathRefDes( node_path, top_file ):
    save_topo_file = lt.GetTopologyFile()
    lt.SetTopologyFile( top_file )

    path_refDes = [ lt.LookupRefDes( node ) for node in node_path ]

    # restore topology file for lookup api in case it was a different one
    lt.SetTopologyFile( save_topo_file )
    return path_refDes

def ConnectionPaths():
    return connectionPaths.copy()