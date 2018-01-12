# smear-pheno

Follow instructions from [install-pheno](https://github.com/kpedro88/install-pheno), then:
```
source init.(c)sh
git clone git@github.com:kpedro88/smear-pheno.git
cd smear-pheno
make runPythia
```

To run Pythia8:
```
./runPythia pythia_QCD_Pt800to1000.cmnd
```

To run Delphes:
```
$LOCAL/delphes/install/bin/DelphesHepMC delphes_card_CMS_smear.tcl qcd.root hepmc.out
```
