# dmx over ethernet via python

import socket
import time

KINET_MAGIC=chr(0x04)+chr(0x01)+chr(0xdc)+chr(0x4a)
KINET_VERSION=chr(0x01)+chr(0x00)
KINET_TYPE_DMXOUT=chr(0x01)+chr(0x01)

class DmxConnection :
    def __init__(self, address, port, dmx_port) :
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
        self.sock.connect((address,port))
        self.dmx_port = dmx_port

    def send_dmx(self, data) :
        out=KINET_MAGIC+KINET_VERSION+KINET_TYPE_DMXOUT
        out+=chr(0x00)+chr(0x00)+chr(0x00)+chr(0x00) #seq
        out+=chr(self.dmx_port) #port number
        out+=chr(0x00) #flags
        out+=chr(0x00)+chr(0x00) # timerVal
        out+=chr(0xFF)+chr(0xFF)+chr(0xFF)+chr(0xFF) # uni
        out+=data
        if(len(out)!=self.sock.send(out)) :
            print "socket problem"
            raise SystemExit(1)

class RGBLight :
    def __init__(self) :
        self.r = 0
        self.g = 0
        self.b = 0

    def setrgb(self, r, g, b) :
        self.r = r
        self.g = g
        self.b = b
    
    # h,s,b are from 0 to 1
    def sethue(self, hue, brightness, saturation) :
        angle = hue*6%6.0
        brightness = min(max(float(brightness), 0.0), 1.0)
        saturation = min(max(float(saturation), 0.0), 1.0)
        if angle<2.0 :
            self.r=1
            if angle<1.0 :
                self.g = 0
                self.b = 1.0-angle
            else :
                self.g = angle-1.0
                self.b = 0
        if angle>=2.0 and angle<4.0 :
            self.g=1
            if angle<3.0 :
                self.r=3.0-angle
                self.b=0
            else :
                self.r=0
                self.b=angle-3.0
        if angle>=4.0 :
            self.b=1
            if angle<5.0 :
                self.g=5.0-angle
                self.r=0
            else :
                self.g=0
                self.r=angle-5.0
        self.r=brightness*(min(max(brightness-saturation, 0.0), 1.0)*self.r+saturation)
        self.g=brightness*(min(max(brightness-saturation, 0.0), 1.0)*self.g+saturation)
        self.b=brightness*(min(max(brightness-saturation, 0.0), 1.0)*self.b+saturation)

class LightPanel :
    def __init__(self, address, port, dmx_port) :
        self.lights = [[RGBLight() for i in range(0,12)]
                       for j in range(0,12)]
        self.dmx = DmxConnection(address, port, dmx_port)
        self.width = 12
        self.height = 12
    def output(self) :
        out = chr(0x00)
        colors = [0 for i in range(0,500)]
        for c in range(0,6) :
            for r in range(0,12) :
                colors[3*(r+12*(5-c))+0]=self.lights[r][c].r
                colors[3*(r+12*(5-c))+1]=self.lights[r][c].g
                colors[3*(r+12*(5-c))+2]=self.lights[r][c].b
        for c in range(6,12) :
            for r in range(0,12) :
                colors[3*(r+12*c)-3+0]=self.lights[r][c].r
                colors[3*(r+12*c)-3+1]=self.lights[r][c].g
                colors[3*(r+12*c)-3+2]=self.lights[r][c].b
        for i in range(0,len(colors)) :
            out+=chr(int(255*min(max(float(colors[i]),0),1.0)))
        while(len(out)<512) :
            out+=chr(0x00)
        out+=chr(255)+chr(191)
        self.dmx.send_dmx(out)

    def outputAndWait(self, fps) :
        self.output()
        time.sleep(1.0/fps)

class LightCompositeHelper :
    def __init__(self, panels, panellocs) :
        self.panels = panels
        self.panellocs = panellocs
    def __getitem__(self, row) :
        a=[(panel,loc) for panel,loc in zip(self.panels, self.panellocs) if row>=loc[0] and row<loc[0]+panel.height]
        p,l = zip(*a)
        return LightCompositeColumnHelper(row,p,l)

class LightCompositeColumnHelper :
    def __init__(self, row, panels, panellocs) :
        self.panels = panels
        self.panellocs = panellocs
        self.row = row
    def __getitem__(self, col) :
        for panel,loc in zip(self.panels, self.panellocs) :
            if col>=loc[1] and col<loc[1]+panel.width :
                return panel.lights[self.row-loc[0]][col-loc[1]]
    def __setitem__(self, col, v) :
        for panel,loc in zip(self.panels, self.panellocs) :
            if col>=loc[1] and col<loc[1]+panel.width :
                panel.lights[self.row-loc[0]][col-loc[1]] = v
                break

class PanelComposite :
    def __init__(self) :
        self.panels = []
        self.panelloc = []
        self.lights = LightCompositeHelper(self.panels, self.panelloc)
    def addPanel(self, panel, llrow, llcol) :
        self.panels.append(panel)
        self.panelloc.append((llrow, llcol))
    def output(self) :
        for panel in self.panels :
            panel.output()
    def outputAndWait(self, fps) :
        self.output()
        time.sleep(1.0/fps)

if __name__=="__main__" :
    panel = LightPanel("18.224.3.100", 6038, 0)
    a = PanelComposite()
    a.addPanel(panel, 0, 0)
    for y in range(0,12) :
        for x in range(0,12) :
            a.lights[y][x].r=1.0
            a.output()
            time.sleep(1.0/20)
    for y in range(0,12) :
        for x in range(0,12) :
            a.lights[y][x].g=1.0
            a.output()
            time.sleep(1.0/20)
    for y in range(0,12) :
        for x in range(0,12) :
            a.lights[y][x].b=1.0
            a.output()
            time.sleep(1.0/20)
