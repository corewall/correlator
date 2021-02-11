import xml.sax.handler

class XMLHandler(xml.sax.handler.ContentHandler):
    def __init__(self):
        self.type = ""
        self.site = ""
        self.leg = ""
        self.datatype = ""
        self.hole = ""
        self.core = ""
        self.fout = None
        self.splice_flag = False
        self.count = 0
        self.backup = [] 

    def init(self):
        self.type = ""
        self.site = ""
        self.leg = ""
        self.datatype = ""
        self.hole = ""
        self.core = ""
        self.fout = None
        self.splice_flag = False
        self.count = 0
        self.backup = [] 

    def openFile(self, filename):
        self.fout = open(filename, 'w+')

    def closeFile(self):
        self.fout.close()
        self.fout = None

    def startElement(self, name, attributes):
        if name == "Data":
            self.type = attributes["type"]
            if self.type != "age depth"  :
                self.leg = attributes["leg"]
                self.site =  attributes["site"]

            if self.type == "affine table" :
                self.fout.write("# Leg, Site, Hole, Core No, Section Type, Depth Offset, Y/N\n")
                self.fout.write("# Generated By Correlator\n")
            elif self.type == "splice table" :
                self.fout.write("# Site, Hole, Core No, Section Type, Section No, Top, Bottom, Mbsf, Mcd, TIE/APPEND Site, Hole, Core No, Section Type, Section No, Top, Bottom, Mbsf, Mcd\n")
                affinetable = "None"
                keys = attributes.keys()
                for key in keys :
                    if key == "affinefilename" :
                        affinetable =  attributes["affinefilename"]
                        break

                self.fout.write("# AffineTable " + affinetable + "\n")
                self.fout.write("# Generated By Correlator\n")
            elif self.type == "cull table" :
                self.datatype =  attributes["datatype"]
                self.fout.write("# Leg Site Hole Core No Section_Type Section_No Top Bottom\n")
                self.fout.write("# Leg Site Hole Core No badcore\n")
                cull_top =  attributes["cull_top"]
                self.fout.write("# Top " + cull_top + "\n")

                cull_range =  attributes["cull_range"]
                if cull_range != "" :
                    range_token = cull_range.split(' ')
                    range_str = ""
                    if range_token[0] == 'greater' :
                        range_str ="> "
                    else :
                        range_str ="< "
                    range_str += range_token[1]
                    if len(range_token) > 2 :
                        if range_token[2] == 'greater' :
                            range_str +=" > "
                        else :
                            range_str +=" < "
                        range_str += range_token[3]
                    self.fout.write("# Range " +  range_str + "\n")

                self.fout.write("# Type " + self.datatype + "\n")
                self.fout.write("# Generated By Correlator\n")
            elif self.type == "core data" :
                self.datatype =  attributes["datatype"]
            elif self.type == "eld table" :
                str_line = "Equivalent Log Depth Table: \tLeg \t" + self.leg + " \tSite \t" + self.site + "\n"
                self.fout.write(str_line)
                str_line = "Overall \t" + attributes["applied"] + " \tMudlineOffset \t" + attributes["mudlineoffset"] + " \tStretch/Compress \t" + attributes["stretchrate"] + "\n"
                self.fout.write(str_line)
                keys = attributes.keys()
                affine_flag = False
                for key in keys :
                    if key == "affinetable" :
                        affine_flag = True 
                        break
                if affine_flag == True :
                    str_line = "Affine \tY \t" + attributes["affinetable"] + "\n"
                else :
                    str_line = "Affine \tN\n"
                self.fout.write(str_line)
            elif self.type == "age depth" :
                #self.fout.write("# Mbsf, Mcd, Eld, Age, Sediment rate, Age datum name, Label, type\n")
                self.fout.write("# Depth  Age Control Point Comment\n")
                self.fout.write("# Generated By Correlator\n")
            elif self.type == "age model" :
                self.fout.write("# Leg, Site, Mbsf, Mcd, Eld, Age, Sediment Rate, Age Datum, Comment, Type \n")
                self.fout.write("# Generated By Correlator\n")

        elif name == "Hole":
            self.hole =  attributes["value"]
        elif name == "Core":
            if self.type == "affine table" :
                self.core = attributes["id"]
                str_line = self.leg + " \t" + self.site + " \t" +  self.hole + " \t" + attributes["id"] + " \t" + attributes["type"] + " \t" + attributes["offset"] + " \t" + attributes["applied"] + "\n"
                self.fout.write(str_line)
            elif self.type == "splice table" :
                self.parseSplice(attributes)
            elif self.type == "eld table" :
                self.core = attributes["id"]
                self.count = 0
                self.parseELD(attributes)
            elif self.type == "cull table" :
                self.core = attributes["id"]
                keys = attributes.keys()
                for key in keys :
                    if key == "flag" :
                        str_line = self.leg + " \t" + self.site + " \t" +  self.hole + " \t" + self.core + " \t" + attributes["flag"] + "\n"
                        self.fout.write(str_line)
                        break
                    else :
                        self.core = attributes["id"]
                                
        elif name == "LogTie":
            self.count += 1 
            self.parseLogTie(attributes)
        elif name == "Value":
            if self.type == "core data" :
                self.parseCore(attributes)
            elif self.type == "cull table" :
                str_line = self.leg + " \t" + self.site + " \t" +  self.hole + " \t" + self.core + " \t" + attributes["type"] + " \t" + attributes["section"] + " \t" + attributes["top"] + " \t" + attributes["bottom"] + "\n"
                self.fout.write(str_line)
        elif name == "Stratigraphy":
            if self.type == "age depth" :
                label = attributes["controlpoint"]
                if label == "" :
                    label = "X"
                type = attributes["type"]
                if type == "" :
                    type = "Handpick"
                str_line = attributes["depth"] + " \t" + attributes["age"] + " \t" + label+ " " + type + "\n"
                self.fout.write(str_line)
            else :
                str_line = str(self.leg) + " \t" + str(self.site) + " \t" + attributes["mbsf"] + " \t" + attributes["mcd"] + " \t" + attributes["eld"] + " \t" + attributes["age"] + " \t" + attributes["sedrate"] + " \t" +  attributes["agedatum"] + " \t" + attributes["comment"] + " \t" + attributes["type"] + " \t" + "\n"
                self.fout.write(str_line)
            

    def characters(self, data):
        pass
    
    def endElement(self, name):
        if name == "Core":
            if self.type == "eld table" :
                str_line = str(self.count) + "\n"
                self.fout.write(str_line)
                for tie in self.backup :
                    str_line = self.site + " \t" + self.hole + " \t" + self.core + " \t"
                    self.fout.write(str_line)
                    str_line = tie[0] + " \t" + tie[1] + " \t" + tie[2] + " \t" + tie[3] + " \t"
                    self.fout.write(str_line)
                    str_line = tie[4] + " \t" + tie[5] + " \t" + tie[6] + " \t" + tie[7] + " \t" + tie[8] + " \t" + tie[9] + "\n"  
                    self.fout.write(str_line)
                self.backup  = []

    def parseSplice(self, attributes):
        if self.splice_flag == False :
            str_line = self.site + " \t" + attributes["hole"] + " \t" + attributes["id"] + " \t" + attributes["type"] + " \t" + attributes["section"] + " \t" + attributes["top"] + " \t" + attributes["bottom"] + " \t" + attributes["mbsf"] + " \t" + attributes["mcd"]
            self.fout.write(str_line)
            self.splice_flag = True 
        else :
            if attributes["tietype"] == "tied" :
                str_line = " \tTIE"
            else :
                str_line = " \tAPPEND"
            self.fout.write(str_line)

            keys = attributes.keys()
            id_flag = False
            for key in keys :
                if key == "id" :
                    id_flag = True
                    self.core = attributes["id"]
                    break
            if id_flag == False :
                str_line = "\n"
            else :
                str_line = " \t" + self.site + " \t" + attributes["hole"]  + " \t" + attributes["id"] + " \t" + attributes["type"] + " \t" + attributes["section"] + " \t" + attributes["top"] + " \t" + attributes["bottom"] + " \t" + attributes["mbsf"] + " \t" + attributes["mcd"] + "\n"
            self.fout.write(str_line)
            self.splice_flag = False 

    def parseELD(self, attributes):
        str_line = "Hole \t" + self.hole + " \tCore \t" + self.core + " \tAffineOffset \t" + attributes["offset"] + " \t" + attributes["applied"] + " \t#Ties \t"
        self.fout.write(str_line)

    def parseLogTie(self, attributes):
        l = []
        l = attributes["type"], attributes["section"], attributes["bottom"], attributes["top"], attributes["mbsf"], attributes["mcd"], attributes["a"], attributes["b"], attributes["share"], attributes["eld"]
        self.backup.append(l)

    def parseCore(self, attributes):
        age_flag = False
        annotation_flag = False
        keys = attributes.keys()
        for key in keys :
            if key == "age" :
                age_flag = True 
                break
            if key == "annotation" :
                annotation_flag = True 
                break

        if age_flag == False :
            if annotation_flag == True  :
                str_line = self.leg + " \t" +  self.site + " \t" + self.hole + " \t" + self.core + " \t" + attributes["type"] + " \t" + attributes["section"] + " \t" + attributes["top"] + " \t" + attributes["bottom"] + " \t" + attributes["depth"] + " \t" + attributes["data"] + " \t- \t" + attributes["annotation"] + "\n"
            else :
                str_line = self.leg + " \t" +  self.site + " \t" + self.hole + " \t" + self.core + " \t" + attributes["type"] + " \t" + attributes["section"] + " \t" + attributes["top"] + " \t" + attributes["bottom"] + " \t" + attributes["depth"] + " \t" + attributes["data"] + "\n"
            self.fout.write(str_line)
        else :
            str_line = self.leg + " \t" +  self.site + " \t" + self.hole + " \t" + self.core + " \t" + attributes["type"] + " \t" + attributes["section"] + " \t" + attributes["top"] + " \t" + attributes["bottom"] + " \t" + attributes["depth"] + " \t" + attributes["data"] + " \t" + attributes["sedrate"] + " \t" + attributes["depth2"] + " \t" + attributes["age"] + "\n"
            self.fout.write(str_line)

