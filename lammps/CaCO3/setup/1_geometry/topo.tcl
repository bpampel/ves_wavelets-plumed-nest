# vmd script to create geometry file while adding missing angles and bondtypes

set boxlength 42.0
pbc set [list $boxlength $boxlength $boxlength]

package require topotools
# distinguish between the two bond types
topo retypebonds
# identify all angles H2-O2, C4-O4
topo guessangles
# detect improper at O4-O4-C4-O4
topo guessimpropers
topo writelammpsdata data.CaCO3
