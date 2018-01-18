#!/bin/bash

for i in 02 04 06 08 10; do
	echo 'set ResolutionFormula { 0.'${i}' }' > jetSmearing.tcl
	cat jetSmearing.tcl
	FILE=qcd${i}.root
	rm $FILE
	$LOCAL/delphes/install/bin/DelphesHepMC delphes_card_CMS_smear.tcl $FILE hepmc.out > log_qcd${i}.log 2>&1
done
