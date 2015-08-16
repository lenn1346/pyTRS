# -*- coding: utf-8 -*-
"""
Created on Fri Jul 31 18:08:12 2015

@author: user
"""

from numpy import sin, sqrt, pi, array
#from math import pow


class Rectifier:
    def __init__(self, *args, **kwds):
        # Parameters entered by user
        self.NominalPower = 2500000
        self.ReqNomVoltage = 750  # Required nominal voltage
        self.M = 2                # Number of groups in series
        self.N = 1	              # Number of groups in parrallel
        self.P = 3                # Number of Phases
        self.S = 2	              # S=1 for single way, S=2 for double way
        self.delta = 0	     # Number of simultaneous commutations per primary.
        self.Vo = 0	              # Diode Threshold voltage
        self.Vrr = 0	          # Rectifier Resistive volt drop per arm
        self.Vxr = 0	          # Rectifier reactive volt drop per arm
        self.PercentReg = 0       # percentage regulation

    def GetIBasic(self):          # Rectifier Resistive volt drop
        if self.ReqNomVoltage == 0:
            print('error: ReqNomVoltage must not equal')
            return 0
        else:
            return self.NominalPower / self.ReqNomVoltage

    def GetVdl(self):   # Light load voltage
        return self.PercentReg * self.ReqNomVoltage

    def GetVdo(self):   # Ideal no load voltage = Vdl + M*S*Vo
        return self.GetVdl() + self.M * self.S * self.Vo

    def GetQ(self):     # Q=Pulse number = (N*M*P*S)/delta
        return (self.N * self.M * self.P * self.S)/self.delta

    def GetExr(self):   # rectifier reactive volt drop = M*S*Vxr
        return self.M * self.S * self.Vxr

    def GetErrNominal(self):  # Nominal Rectifier Resistive volt drop = Vrr*M*S
        return self.Vrr * self.M * self.S

    def MPS(self):
        return self.M * self.P * self.S

    def GetXrNominal(self, inTxfr, inRect):  # rectifier reactance (in percent)
        return self.GetExr()/GetReactiveVoltMultiplier(inTxfr, inRect)

    def GetXr(self, inTxfr, inRect, inTol):
        return inTol.GetTolerance(self.GetXrNominal(inTxfr, inRect),
                                  inTol.Xr, 0)

    def GetRr(self, inTxfr):
        return (self.GetErrNominal() * self.GetIBasic() /
                inTxfr.GetPdo(self) * 100)

    def GetdcVoltDrop(self, inSupply, inTxfr):
        return inSupply.GetExs(inTxfr, self) + inTxfr.GetExt(self)
        + self.GetExr() + inSupply.GetErs(inTxfr, self)
        + inTxfr.GetErtNominal(self) + self.GetErrNominal()
        + self.M * self.S * self.Vo

    def GetCalculatedNominalVoltage(self, inSupply, inTxfr):
        return self.GetVdo() - self.GetdcVoltDrop(inSupply, inTxfr)

    def GetErr(self, inTol):
        return inTol.GetTolerance(self.GetErrNominal(), inTol.Err, False)

    def GetDiodeVoltDrop(self):
        return self.M * self.S * self.Vo


class Supply:
    def __init__(self, *args, **kwds):
        self.Frequency = 50  # Hz
        self.ShortCircuitCapacity = 250000000  # VA
        self.Voltage = 11000
        self.NumTRUs = 1
        self.X2RKnown = 0
        self.X2R = 1000
        #self.Zs = 0      #Supply impedance(in percent) = Transformer.Pdo*100/ShortCircuitCapacity
        #self.Xs = 0      #supply reactance(in percent) = Zs/sqrt(1+X2R^-2)
        #self.Rs = 0      #supply resistance(in percent) = Xs/X2R
        #self.Exs = 0     #supply reactive volts drop = Xs*ReactiveVoltMultiplier(Rectifier,Transformer)
        #self.Ers = 0     #Supply resistive volt drop = (Rs/100)*(Transformer.Pdo/Rectifier.IBasic)

    def GetZs(self, inTxfr, inRect):
        # Supply impedance(in percent) =
        #     Transformer.Pdo*100/ShortCircuitCapacity
        return inTxfr.GetPdo(inRect) * 100 / self.ShortCircuitCapacity

    def GetXs(self, inTxfr, inRect):
        # supply reactance(in percent) = Zs/sqrt(1+X2R^-2)
        return self.GetZs(inTxfr, inRect) / sqrt(1 + pow(self.X2R, -2))

    def GetRs(self, inTxfr, inRect):
        # supply resistance(in percent) = Xs/X2R
        return self.GetXs(inTxfr, inRect) / self.X2R

    def GetExs(self, inTxfr, inRect):
        # supply reactive volts drop =
        # Xs*ReactiveVoltMultiplier(Rectifier,Transformer)
        return (self.GetXs(inTxfr, inRect) *
                GetReactiveVoltMultiplier(inTxfr, inRect))

    def GetErs(self, inTxfr, inRect):
        # Supply resistive volt drop =
        # (Rs/100)*(Transformer.Pdo/Rectifier.IBasic)
        return ((self.GetRs(inTxfr, inRect) / 100) *
                (inTxfr.GetPdo(inRect)/inRect.GetIBasic()))


class System:
    def GetKsys(self, inSupply, inTxfr, inRect):  # system coupling factor Ksys
        return (inSupply.GetXs(inTxfr, inRect) +
                inTxfr.GetXpri()) / (inSupply.GetXs(inTxfr, inRect) +
                                     inTxfr.GetXpri() + inTxfr.GetXsec() +
                                     inRect.GetXrNominal(inTxfr, inRect))

    def GetVdoMax(self, inRect, inTol):  # Max no load voltage
        return inRect.GetVdo() * (1 + inTol.TurnsRatio / 100)

    def GetVdoMin(self, inRect, inTol):  # Max no load voltage
        return inRect.GetVdo() * (1 - inTol.TurnsRatio / 100)

    def GetVDMax(self, inSupply, inTxfr, inRect, inTol):
        # Max full load volt drop
        return inSupply.GetExs(inTxfr, inRect)
        + inTxfr.GetExt(inRect) * (1 + inTol.Xt / 100)
        + inTxfr.GetErtNominal(inRect) * (1 + inTol.CuLoss / 100)
        + inSupply.GetErs(inTxfr, inRect)
        + inRect.GetExr() * (1 + inTol.Exr / 100)
        + inRect.GetErrNominal() * (1 + inTol.Err/100)
        + inRect.M*inRect.S*inRect.Vo

    def GetVdcMin(self, inSupply, inTxfr, inRect, inTol):
        # Min full load dc voltage
        return self.GetVdoMin(inRect, inTol)
        - self.GetVDMax(inSupply, inTxfr, inRect, inTol)

    def GetVDMin(self, inSupply, inTxfr, inRect, inTol):
        # Min full load volt drop
        return inSupply.GetExs(inTxfr, inRect)
        + inTxfr.GetExt(inRect) * (1 - inTol.Xt / 100)
        + inTxfr.GetErtNominal(inRect) * (1 - inTol.CuLoss / 100)
        + inSupply.GetErs(inTxfr, inRect)
        + inRect.GetExr() * (1 - inTol.Exr / 100)
        + inRect.GetErrNominal() * (1 - inTol.Err / 100)
        + inRect.M * inRect.S * inRect.Vo

    def GetVdcMax(self, inSupply, inTxfr, inRect, inTol):
        # Max full load dc voltage
        return self.GetVdoMax(inRect, inTol)
        - self.GetVDMin(inSupply, inTxfr, inRect, inTol)

    def GetVdc(self, inRect, inTol):  # is this Ideal no load direct voltage?
        return inTol.GetTolerance(inRect.GetVdo(), inTol.Vdo, True)

    def GetVdl(self, inRect, inTol):
        # what is Vdl, is this conventional no load direct voltage?
        return self.GetVdc(inRect, inTol) - inRect.GetDiodeVoltDrop()

    def GetXc(self, inSupply, inTxfr, inRect, inTol):  # (Ohms, nominal)
        return (((inSupply.GetXs(inTxfr, inRect) +
                inTxfr.GetXt(inTol) +
                inRect.GetXr(inTxfr, inRect, inTol)) / 100) * (pi / 2) *
                ((3 * inRect.GetQ()) / ((pow(inRect.M, 2)) *
                                        (pow(inRect.P, 2)) *
                                        (pow(inRect.S, 2)))) *
                (sin(pi/inRect.GetQ())/(pow((sin(pi/inRect.P)), 2))) *
                (inRect.GetVdo()/inRect.GetIBasic()))


class Transformer:
    def __init__(self, *args, **kwds):
        self.XtNominal = 0
        self.CuLoss = 25    # Full load loss (Cu loss) kW
        self.FeLoss = 4     # No load loss (Fe loss) kW
        self.IMag = 0       # Magnetising Current %
        self.Kt = 0.85      # Txfr secondry coupling factor (Kt) PU

    def GetXpri(self):
        return self.XtNominal * self.Kt

    def GetXsec(self):
        return self.XtNominal - self.GetXpri()

    def GetExt(self, inRect):  # transformer reactive volts drop
        return self.XtNominal * GetReactiveVoltMultiplier(self, inRect)

    def GetXt(self, inTol):
        # Transformer percentage reactance based on full primary kVA
        # Original TRS had this tolerance always set to 10)
        return inTol.GetTolerance(self.XtNominal, inTol.Xt, False)

    def GetXct(self, inRect):
        # Calculate anode to neutral comutating reactance (Ohms)
        return ((self.XtNominal / 100) * (pi / 2) *
                ((3 * inRect.GetQ()) / (pow(inRect.M, 2) * pow(inRect.P, 2) *
                                        pow(inRect.S, 2))) *
                (sin(pi / inRect.GetQ()) / (pow(sin(pi / inRect.P), 2))) *
                (inRect.GetVdo() / inRect.GetIBasic()))

    def GetPdo(self, inRect):  # Transformer rated primary VA base (VA)
        return ((pi/(inRect.GetQ() * sin(pi/inRect.GetQ()))) *
                inRect.GetVdo() * inRect.GetIBasic())  # (VA)

    def GetErtNominal(self, inRect):
        # Transformer resistive volt drop (in percent)
        return self.CuLoss/inRect.GetIBasic()

    def GetErt(self, inTol, inRect):
        return inTol.GetTolerance(self.GetErtNominal(inRect), inTol.Ert, False)

    def GetRt(self, inRect):  # (in percent)
        return (self.GetErtNominal(inRect) *
                (inRect.GetIBasic() / self.GetPdo(inRect)) * 100)

    def GetEs(self, inRect):  # Transformer secondary line voltage: ANSI C34.2
        return ((sqrt(3) * inRect.GetVdo()) /
                (inRect.MPS()*(sqrt(2)/pi)*(sin(pi/inRect.P))))


class Tolerances:
    def __init__(self, *args, **kwds):
        self.Xt = 7.5         # % tolerance on txfr reactance (7.5 for BS171)
        self.CuLoss = 10      # % tolerance on txfr load loss (10 for BS171)
        # % tolerance on txfr turns ratio (HV:LV)
        self.TurnsRatio = 0   # (0.5 for BS171)
        self.Err = 0          # % tolerance on rectifier resistive volts drop
        self.Exr = 0          # % tolerance on rectifier reactive volts drop
        self.Ert = 0          # % tolerance on transformer resistive volt drop
        self.Vdo = 0          # % tolerance on Ideal no load voltage
        self.Xr = 0           # % tolerance on rectifier reactance

    def GetTolerance(self, inThing, inTol, rev):
        # gives tolerences for a number and percentage tolerance
        if rev:
            out = array([inThing*(1+inTol/100), inThing,
                         inThing*(1-inTol/100)])
        else:
            out = array([inThing*(1-inTol/100), inThing,
                         inThing*(1+inTol/100)])
        return out


def GetReactiveVoltMultiplier(inTxfr, inRect):
    return ((inRect.MPS() / (2 * pi * inRect.N)) *
            (inTxfr.GetXct(inRect)/inTxfr.XtNominal) * inRect.GetIBasic())
