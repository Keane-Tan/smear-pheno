from argparse import ArgumentParser
from array import array

class Sample(object):
    def __init__(self,name,filename,smear=0.0,color=1,style=1,opt="l"):
        self.name = name
        self.nameCleaned = name.replace(" ","_").replace("(","_").replace(")","_").replace(".","_")
        self.filename = filename
        self.treename = ""
            
        self.color = color
        self.style = style
        self.smear = smear
        self.opt = opt
        
        # changed in descendant classes
        self.jetDraw = ""
        self.metDraw = ""
        
        # defaults
        self.jetHisto = None
        self.metHisto = None
        
    def initialize(self):
        if len(self.filename)>0:
            self.file = TFile.Open(self.filename)
        else:
            self.file = None
        
        if self.file is not None and len(self.treename)>0:
            self.tree = self.file.Get(self.treename)
        else:
            self.tree = None
        
    def run(self):
        if self.tree is None:
            raise ValueError("No tree in sample "+sample.name)
        # generate plots/values
        self.makeJetHisto()
        self.makeMetHisto()
        self.eff = self.getMetEff()
        
    def makeJetHisto(self):
        if len(self.jetDraw)==0: return
        hname = "h_jet_"+self.nameCleaned
        self.tree.Draw(self.jetDraw+">>"+hname+"(100,0,2000)","","goff")
        self.jetHisto = gDirectory.Get(hname)
        self.normalizeHisto(self.jetHisto)
        self.jetHisto.GetXaxis().SetTitle("jet p_{T} [GeV]")
        
    def makeMetHisto(self):
        if len(self.metDraw)==0: return
        hname = "h_met_"+self.nameCleaned
        self.tree.Draw(self.metDraw+">>"+hname+"(100,0,700)","","goff")
        self.metHisto = gDirectory.Get(hname)
        self.normalizeHisto(self.metHisto)
        self.metHisto.GetXaxis().SetTitle("H_{T}^{miss} [GeV]")
        
    def getMetEff(self):
        if len(self.metDraw)==0: return
        denom = self.tree.Draw(self.metDraw,"","goff")
        numer = self.tree.Draw(self.metDraw,self.metDraw+">200","goff")
        return float(numer)/float(denom)
        
    def normalizeHisto(self,h):
        h.Scale(1.0/h.Integral(0,h.GetNbinsX()))
        h.SetLineColor(self.color)
        h.SetLineStyle(self.style)
        h.SetTitle("")
        h.GetYaxis().SetTitle("arbitrary units")
        
class SampleDelphes(Sample):
    def __init__(self,name,filename,smear=0.0,color=1,style=1,opt="l"):
        super(SampleDelphes,self).__init__(name,filename,smear,color,style,opt)
        self.treename = "Delphes"
        
class SampleDelphesUnsmeared(SampleDelphes):
    def __init__(self,name,filename,smear=0.0,color=1,style=1,opt="l"):
        super(SampleDelphesUnsmeared,self).__init__(name,filename,smear,color,style,opt)
        self.jetDraw = "JetUnsmeared.PT"
        self.metDraw = "MissingHT.MET"
        
class SampleDelphesSmeared(SampleDelphes):
    def __init__(self,name,filename,smear=0.0,color=1,style=1,opt="l"):
        super(SampleDelphesSmeared,self).__init__(name,filename,smear,color,style,opt)
        self.jetDraw = "JetSmeared.PT"
        self.metDraw = "MissingHTSmeared.MET"

class SampleCMS(Sample):
    def __init__(self,name,filename,smear=0.0,color=1,style=1,opt="l"):
        super(SampleCMS,self).__init__(name,filename,smear,color,style,opt)
        self.treename = "TreeMaker2/PreSelection"
        self.jetDraw = "Jets.Pt()"
        self.metDraw = "MHT"
    
def getRange(samples,attr,logy=False):
    y1 = 1.0e100
    y2 = 0.0
    for sample in samples:
        h = getattr(sample,attr)
        max = h.GetMaximum()
        min = h.GetMinimum()
        if logy: min = h.GetMinimum(0.0)
        if max>y2: y2 = max
        if min<y1: y1 = min
    return (y1,y2)

def makeLegend(samples,attr,left=False):
        x1 = 0.55
        x2 = 0.9
        if left:
            x1 = 0.15
            x2 = 0.55
        leg = TLegend(x1,0.87-0.04*(len(samples)+1),x2,0.87)
        leg.SetMargin(0.15)
        leg.SetFillColor(0);
        leg.SetBorderSize(0);
        leg.SetTextSize(0.04);
        leg.SetTextFont(42);
        
        leg.AddEntry(None,"QCD p_{T} 800 to 1000","")
        for sample in samples:
            leg.AddEntry(getattr(sample,attr),sample.name,sample.opt)
            
        return leg

# main program    
if __name__=="__main__":
    # input arguments
    parser = ArgumentParser()
    parser.add_argument("-s","--smearings",dest="smearings",type=str,help="comma-separated list of smearing values")
    args = parser.parse_args()
    
    # check argument and make into list
    if len(args.smearings)==0:
        parser.error("Must specify at least one smearing value")
    smearlist = args.smearings.split(',')

    # import root after parsing arguments
    from ROOT import *

    gStyle.SetOptStat(0)

    # set up samples
    samples = [
        SampleCMS("CMS FullSim","root://cmseos.fnal.gov//store/user/lpcsusyhad/SusyRA2Analysis2015/Run2ProductionV14/Summer16.QCD_Pt_800to1000_TuneCUETP8M1_13TeV_pythia8_0_RA2AnalysisTree.root",color=kBlack,style=7),
        SampleDelphesUnsmeared("Delphes (unsmeared)","qcd"+smearlist[0]+".root",color=kGray+2,style=1)
    ]
    colors = [kMagenta+2,kMagenta,kBlue,kRed,kOrange+1]
    for i,num in enumerate(smearlist):
        samples.append(SampleDelphesSmeared("Delphes (smeared 0."+num+")","qcd"+num+".root",smear=float("0."+num),color=colors[i],style=1))
        
    for sample in samples:
        sample.initialize()
        sample.run()
        
    # jet plot
    
    jetCan = TCanvas("jetpt","jetpt")
    jetCan.SetLogy()
    jetCan.cd()
    jetLeg = makeLegend(samples,"jetHisto")
    y1,y2 = getRange(samples,"jetHisto",logy=True)
    
    first = True
    for sample in samples:
        if first:
            sample.jetHisto.GetYaxis().SetRangeUser(y1,y2)
            sample.jetHisto.Draw("hist")
            first = False
        else:
            sample.jetHisto.Draw("hist same")
    jetLeg.Draw("same")
    
    jetCan.Print("jetpt_"+args.smearings+".png","png")
    
    # met plot
    
    metCan = TCanvas("met","met")
    metCan.cd()
    metLeg = makeLegend(samples,"metHisto")
    y1,y2 = getRange(samples,"metHisto")
    
    first = True
    for sample in samples:
        if first:
            sample.metHisto.GetYaxis().SetRangeUser(y1,y2)
            sample.metHisto.Draw("hist")
            first = False
        else:
            sample.metHisto.Draw("hist same")
    metLeg.Draw("same")
    
    metCan.Print("met_"+args.smearings+".png","png")
    
    # met eff graph
    
    x, y = array('d'), array('d')
    for sample in samples[1:]:
        x.append(sample.smear)
        y.append(sample.eff)
    
    effGraph = TGraph(len(x),x,y)
    effGraph.SetMarkerStyle(20)
    effGraph.SetTitle("")
    effGraph.GetXaxis().SetTitle("smearing [%]")
    effGraph.GetYaxis().SetTitle("efficiency for H_{T}^{miss} > 200 GeV")
  
    effCan = TCanvas("eff","eff")
    effCan.cd()
    effGraph.Draw("ap")
    effCan.Update()
    
    effLine = TLine(effCan.GetUxmin(),samples[0].eff,effCan.GetUxmax(),samples[0].eff)
    effLine.SetLineColor(kRed)
    effLine.SetLineStyle(7)
    
    gsamples = [
        SampleCMS("CMS FullSim","",color=kRed,style=7),
        SampleDelphes("Delphes","",color=kBlack,style=1,opt="p")
    ]
    gsamples[0].effGraph = effLine
    gsamples[1].effGraph = effGraph
    effLeg = makeLegend(gsamples,"effGraph",left=True)

    effLine.Draw("same")
    effLeg.Draw("same")
    
    effCan.Print("eff_"+args.smearings+".png","png")
    