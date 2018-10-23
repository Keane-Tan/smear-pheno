import ROOT as r
import numpy as np
import glob

r.gSystem.Load("libDelphes")
r.gROOT.ProcessLine('.include /uscms_data/d3/keanet/cutflow/Delphes-3.4.1')
r.gInterpreter.Declare('#include "classes/DelphesClasses.h"')
r.gInterpreter.Declare('#include "ExRootAnalysis/ExRootTreeReader.h"')

# useful functions
def eventCounts(aList):
	aList = np.array(aList)
	sumOfaList = np.sum(aList * crossSections)* 1000. * lumi
	return sumOfaList

def trans_mass_Njet(jets, met, metPhi):
    visible = r.TLorentzVector()
    for jet in jets:
        visible += jet
    jetMass2 = visible.M2()
    term1 = r.TMath.Sqrt(jetMass2 + visible.Pt()**2) * met
    term2 = r.TMath.Cos(metPhi-visible.Phi())*visible.Pt()*met
    return r.TMath.Sqrt(jetMass2 + 2*(term1 - term2))

def deltaPhi(fjetPhi,metPhi):
	dphi = fjetPhi - metPhi
	if dphi < -np.pi:
		dphi += 2*np.pi
	if dphi > np.pi:
		dphi -= 2*np.pi

	return abs(dphi)

# all the files
allFiles = sorted(glob.glob('*/qcd_CA11.root'), key=lambda x: int(x[x.find('t')+1:x.find('o')-1])) 

smearPercent = ['0','0','0','09','07','06','05','05','04','03','02','02']

aFwithSmear = []

# Various options for the user
FatJetrequest = raw_input("What kind of jet to use? CA11 or AK8? ")
METrequest = raw_input("Which variable to use to calculate missing ET? MET, MHT, or MHTSmeared? ")

for i in range(len(smearPercent)):
	if smearPercent[i] != '0':
		allFiles[i] = list(allFiles[i])
		allFiles[i][allFiles[i].index(".")] = smearPercent[i] + "."
		allFiles[i] = "".join(allFiles[i])

# above only works because all the directories are named "QCD_Pt(number)to(number)"

# cross sections in pb
crossSections = np.array([2762530.,471100.,117276.,7823.,648.2,186.9,32.293,9.4183,0.84265,0.114943,0.00682981,0.000165445])

# luminosity in fb^-1
lumi = 35.9

# List of the all the efficiencies for all the different pt bins
totEList = []
njEList = []
jEList = []
presEList = []
elecEList = []
lepEList = []
metMTEList = []
fjDEtaEList = []
fjDPhiEList = []

for i in range(len(allFiles)):
	print("Reading " + allFiles[i] + "...")
	tf = r.TFile(allFiles[i])
	tr = tf.Get("Delphes")

	# counters
	totEvent = 0
	njEvent = 0	
	jEvent = 0
	presEvent = 0
	elecEvent = 0	
	lepEvent = 0
	metMTEvent = 0
	fjDEtaEvent = 0
	fjDPhiEvent = 0

	treeReader = r.ExRootTreeReader(tr)
	numberOfEntries = treeReader.GetEntries()
	nGen = float(numberOfEntries) # number of event generated
	
	# All the relevant branches
	branchJet = treeReader.UseBranch("Jet")
	branchElec = treeReader.UseBranch("Electron")
	branchMuon = treeReader.UseBranch("Muon")
	if FatJetrequest == "AK8":
		branchFJet = treeReader.UseBranch("FatJet")
	elif FatJetrequest == "CA11":
		branchFJet = treeReader.UseBranch("FatFastJet")
	if METrequest == "MET":
		branchMET = treeReader.UseBranch("MissingET")
	elif METrequest == "MHT":	
		branchMET = treeReader.UseBranch("MissingHT")
	elif METrequest == "MHTSmeared":	
		branchMET = treeReader.UseBranch("MissingHTSmeared")


	for entry in range(numberOfEntries):
		treeReader.ReadEntry(entry)

	# npass is a variable that gives 1 when an event passes all the selection criteria
		npass = 1
		totEvent += 1
		fjets = [] # for calculating M_T
	# Trigger/preselection
		
	## N_jet >= 2, p_T > 100, |eta| < 2.4
		nJet = branchJet.GetEntriesFast()
		if nJet < 2:
			npass = 0

		if npass == 1:
			njEvent += 1

			Jet1 = branchJet.At(0)
			Jet2 = branchJet.At(1)

			if Jet1.PT <= 100 or Jet2.PT <= 100 or abs(Jet1.Eta) >= 2.4 or abs(Jet2.Eta) >= 2.4:
				npass = 0
		if npass == 1:	
			jEvent += 1

	## Missing E_T > 200
		MET = branchMET.At(0)
		met = MET.MET
		metPhi = MET.Phi # useful for calculating M_T

		if met <= 200:
			npass = 0

		if npass == 1:
			presEvent += 1

	# Lepton veto

	## Electron: p_T > 10, |eta| < 2.4
		nElec = branchElec.GetEntriesFast()
		if nElec != 0:
			for j in range(nElec):
				Elec = branchElec.At(j)
				if Elec.PT > 10 and abs(Elec.Eta) < 2.4:
					npass = 0

		if npass == 1:
			elecEvent += 1

	## Muon: p_T > 10, |eta| < 2.4
		nMuon = branchMuon.GetEntriesFast()
		if nMuon != 0:
			for j in range(nMuon):
				Muon = branchMuon.At(j)
				if Muon.PT > 10 and abs(Muon.Eta) < 2.4:
					npass = 0

		if npass == 1:
			lepEvent += 1

	# Missing E_T/M_T > 0.15
		nFJet = branchFJet.GetEntriesFast()			

		if nFJet < 2:
			npass = 0
		else:
			FJet1 = branchFJet.At(0) # First leading AK8 Jet
			FJet2 = branchFJet.At(1) # Second leading AK8 Jet
			fjet1 = r.TLorentzVector()
			fjet1.SetPtEtaPhiM(FJet1.PT,FJet1.Eta,FJet1.Phi,FJet1.Mass)
			fjet2 = r.TLorentzVector()
			fjet2.SetPtEtaPhiM(FJet2.PT,FJet2.Eta,FJet2.Phi,FJet2.Mass)
			fjets.append(fjet1)
			fjets.append(fjet2)
			MT = trans_mass_Njet(fjets, met, metPhi)
			if met/MT <= 0.15:
				npass = 0

		if npass == 1:
			metMTEvent += 1

	# |Delta Eta| < 1.1 (AK8): Delta Eta between two leading Fat Jets
		if nFJet >= 2:
			FJet1 = branchFJet.At(0)
			FJet2 = branchFJet.At(1)
			if abs(FJet1.Eta-FJet2.Eta) >= 1.1:
				npass = 0

		if npass == 1:
			fjDEtaEvent += 1

	# |Delta Phi| < 0.4 (AK8)
		if nFJet >= 2:
			FJet1 = branchFJet.At(0)
			FJet2 = branchFJet.At(1)
			dphi1 = deltaPhi(FJet1.Phi,metPhi)
			dphi2 = deltaPhi(FJet2.Phi,metPhi)
			if np.amin([dphi1,dphi2]) >= 0.4:
				npass = 0

		if npass == 1:
			fjDPhiEvent += 1

	totEList.append(totEvent/nGen) # Event/numberOfEntries is the efficiency
	njEList.append(njEvent/nGen)
	jEList.append(jEvent/nGen)
	presEList.append(presEvent/nGen) 
	elecEList.append(elecEvent/nGen)
	lepEList.append(lepEvent/nGen)
	metMTEList.append(metMTEvent/nGen)
	fjDEtaEList.append(fjDEtaEvent/nGen)
	fjDPhiEList.append(fjDPhiEvent/nGen)

# results	


print("Total number of QCD events before any cuts is %i \n" % (eventCounts(totEList)))
print("nJet >= 2                                 --> %i" % (eventCounts(njEList)))
print("Jet.PT > 100, abs(Jet.Eta) < 2.4          --> %i" % (eventCounts(jEList)))
print("MET > 200 (all preselection)              --> %i" % (eventCounts(presEList)))
print("electron veto (p_T > 10, |eta| < 2.4)     --> %i" % (eventCounts(elecEList)))
print("muon veto (p_T > 10, |eta| < 2.4)         --> %i" % (eventCounts(lepEList)))
print("met/MT > 0.15                             --> %i" % (eventCounts(metMTEList)))
print("|Delta Eta| < 1.1 ("+FatJetrequest+")                   --> %i" % (eventCounts(fjDEtaEList)))
print("|Delta Phi| < 0.4 ("+FatJetrequest+")                   --> %i \n" % (eventCounts(fjDPhiEList)))

