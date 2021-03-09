import re
import os
from decimal import Decimal

topo_file = ''

def SetTopologyFile( top_file ):
    global topo_file
    topo_file = top_file

def CheckTopologyFileInitialized():
    if not topo_file:
        print( 'Topology file not initialized.' )
        quit()

def GetTopologyFile():
    return topo_file

def LookupComponentType( node_name ):
    CheckTopologyFileInitialized()
    component_type = None

    with open( topo_file , 'r' ) as top:
        # lines = top.readlines()
        # for line in lines:
        while ( line := top.readline() ):
            node_name_match = re.search( r'6624020A\.{0}" (\w+)'.format( node_name ), line )
            if node_name_match:
                component_type = node_name_match.group(1)
        
    return component_type

def LookupRefDes( node_name ):
    CheckTopologyFileInitialized()
    name = None

    with open( topo_file , 'r' ) as top:
        while ( line := top.readline() ):
            node_name_match = re.search( r'6624020A\.({0})"'.format( node_name ), line )
            if node_name_match:
                # skip to line with refDes
                while ( 'refDes' not in (refDes_line := top.readline()) ): continue

                name_match = re.search( r'refDes "([^"]+)"', refDes_line )
                name = name_match.group(1)
                break
        
    return name

def LookupTraceLength( trace ):
    CheckTopologyFileInitialized()
    trace_len = -1
    with open( topo_file , 'r' ) as top:
        while ( line := top.readline() ):
            trace_name_match = re.search( r'6624020A\.({0})"'.format( trace ), line )
            if trace_name_match:
                while '(length "' not in ( trace_len_line := top.readline() ) : continue

                trace_len_match = re.search( r'length "([0-9\.]+) MIL"', trace_len_line )
                # print( trace_len_match.group(1) )
                trace_len = float( trace_len_match.group(1) )
    return trace_len

def LookupProperties( node_name ):
    CheckTopologyFileInitialized()
    props = {}

    with open( topo_file , 'r' ) as top:
        # lines = top.readlines()
        # for line in lines:
        while ( line := top.readline() ):
            node_name_match = re.search( r'6624020A\.({0})"'.format( node_name ), line )
            if node_name_match:
                # skip lines until we reach properties
                while 'Props' not in top.readline():
                    continue
                
                end_props = False
                while True:
                    prop_line = top.readline()
                    # print( prop_line )
                    prop_match = re.search( r'(\w+) "([^"]+)"', prop_line )

                    if prop_match:
                        prop = prop_match.group(1)
                        prop_value = prop_match.group(2)
                        prop_digit = re.findall('\d*\.?\d+', prop_value )
                        print( 'Property: ' + prop + ', digits: ', end='')
                        print( prop_digit[0] )
                        props[ prop ] = { True: prop_value , False: prop_digit[0] } [ len(prop_digit) < 1 ]
                        # print( prop )
                        # print( props[prop])
                    else: #if property value regex does not match, then we're at the end of the properties for this node
                        break
                
    return props
