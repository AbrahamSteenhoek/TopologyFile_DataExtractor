# TopologyFile_DataExtractor

Extracts data from Cadence Allegro Topology files by converting the Topology File into a nodal graph.

When in a nodal graph structure, lots of data from a Topology file can be extracted that involves connections or paths between components. Some examples include:

- Trace (etch) length between any two components in the Topology File
- Number of vias between two components
- How many trace paths between two components
- Variance in trace width for a path between two components, or across the whole topology file
- Number of trace segments that make up a path between two components

This project includes an implementation of calculating the etch length between two components. ```PathLength()```

## Usage

```python .\get_paths.py -n MYNET -s START_COMPONENT -e END_COMPONENT```

## Python Dependencies
- pandas
- numpy
- openpyxl
- tkinter
- argparse
- collections

## Future Work
- Add functionality to combine nodal graphs from two different Topology Files. Theoretically this can turn the whole PCB into one giant nodal graph.
- Add implementations for examples listed above.
