from argparse import ArgumentParser
from array import array

class Histo(object):
    def __init__(self,name="",draw="",bins="",cut="",axis="",effaxis="",logy=False):
        self.name = name
        self.draw = draw
        self.bins = bins
        self.cut = cut
        self.axis = axis
        self.effaxis = effaxis
        self.logy = logy
        self.eff = None
        self.histo = None
        self.effgraph = None

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
        
        # draws changed in descendant classes
        self.histos = {
            "jetpt": Histo(name="jetpt",draw="",bins="(100,0,2000)",cut="",axis="jet p_{T} [GeV]",logy=True),
            "met": Histo(name="met",draw="",bins="(100,0,700)",cut=">200",axis="H_{T}^{miss} [GeV]",effaxis="H_{T}^{miss} > 200 GeV"),
        }
        
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
        for h in self.histos:
            self.makeHisto(self.histos[h])
        
    def makeHisto(self,histo):
        if len(histo.draw)==0: return
        hname = "h_"+histo.name+"_"+self.nameCleaned
        denom = self.tree.Draw(histo.draw+">>"+hname+histo.bins,"","goff")
        histo.histo = gDirectory.Get(hname)
        self.normalizeHisto(histo.histo)
        histo.histo.GetXaxis().SetTitle(histo.axis)
        if len(histo.cut)>0:
            numer = self.tree.Draw(histo.draw+">>"+hname+"_numer"+histo.bins,histo.draw+histo.cut,"goff")
            histo.eff = float(numer)/float(denom)

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
        self.histos["jetpt"].draw = "JetUnsmeared.PT"
        self.histos["met"].draw = "MissingHT.MET"
        
class SampleDelphesSmeared(SampleDelphes):
    def __init__(self,name,filename,smear=0.0,color=1,style=1,opt="l"):
        super(SampleDelphesSmeared,self).__init__(name,filename,smear,color,style,opt)
        self.histos["jetpt"].draw = "JetSmeared.PT"
        self.histos["met"].draw = "MissingHTSmeared.MET"

class SampleCMS(Sample):
    def __init__(self,name,filename,smear=0.0,color=1,style=1,opt="l"):
        super(SampleCMS,self).__init__(name,filename,smear,color,style,opt)
        self.treename = "TreeMaker2/PreSelection"
        self.histos["jetpt"].draw = "Jets.Pt()"
        self.histos["met"].draw = "MHT"
    
def getRange(samples,hist):
    y1 = 1.0e100
    y2 = 0.0
    for sample in samples:
        h = sample.histos[hist].histo
        max = h.GetMaximum()
        min = h.GetMinimum()
        if sample.histos[hist].logy: min = h.GetMinimum(0.0)
        if max>y2: y2 = max
        if min<y1: y1 = min
    return (y1,y2)

def makeLegend(samples,hist,attr="histo",left=False):
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
            leg.AddEntry(getattr(sample.histos[hist],attr),sample.name,sample.opt)
            
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
        
    # plots
    for h in samples[0].histos:
        can = TCanvas(h,h)
        if samples[0].histos[h].logy: can.SetLogy()
        can.cd()
        leg = makeLegend(samples,h)
        y1,y2 = getRange(samples,h)
        
        first = True
        for sample in samples:
            if first:
                sample.histos[h].histo.GetYaxis().SetRangeUser(y1,y2)
                sample.histos[h].histo.Draw("hist")
                first = False
            else:
                sample.histos[h].histo.Draw("hist same")
        leg.Draw("same")
        
        can.Print(h+"_"+args.smearings+".png","png")
        
        # efficiency plot
        if samples[0].histos[h].eff is not None:
            x, y = array('d'), array('d')
            for sample in samples[1:]:
                x.append(sample.smear)
                y.append(sample.histos[h].eff)
            
            effGraph = TGraph(len(x),x,y)
            effGraph.SetMarkerStyle(20)
            effGraph.SetTitle("")
            effGraph.GetXaxis().SetTitle("smearing [%]")
            effGraph.GetYaxis().SetTitle("efficiency for "+samples[0].histos[h].effaxis)
          
            effCan = TCanvas("eff_"+h,"eff_"+h)
            effCan.cd()
            effGraph.Draw("ap")
            effCan.Update()
            
            effLine = TLine(effCan.GetUxmin(),samples[0].histos[h].eff,effCan.GetUxmax(),samples[0].histos[h].eff)
            effLine.SetLineColor(kRed)
            effLine.SetLineStyle(7)
            
            gsamples = [
                SampleCMS("CMS FullSim","",color=kRed,style=7),
                SampleDelphes("Delphes","",color=kBlack,style=1,opt="p")
            ]
            gsamples[0].histos[h].effgraph = effLine
            gsamples[1].histos[h].effgraph = effGraph
            effLeg = makeLegend(gsamples,h,"effgraph",left=True)

            effLine.Draw("same")
            effLeg.Draw("same")
            
            effCan.Print("eff_"+h+"_"+args.smearings+".png","png")

    # fin
    