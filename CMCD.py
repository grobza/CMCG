# -*- coding: utf-8 -*-

import sys
import string

class EnumItem:
    parent = ""
    text = []
    def __init__(self, _parent, _text):
        self.parent = _parent
        self.text = _text

class MenuItem:
    text = ""
    number = 0
    child = ""
    parent = ""
    next = ""
    previous = ""
    name = ""
    variable = ""
    bit = False
    bitInstall = False
    func = False
    funcName = ""
    funcArgument = ""
    varRange = ""
    tempVar = ""
    enum = ""
    valuesNum = 0
    def __init__(self,_text,_child,_parent,_next,_prev,_name, _number):
        #if there is something besides text (variable or func related)
        if string.find(_text, "[")!=-1:
            #gather what is there about it
            varline = _text[(string.find(_text,"[")+1):string.find(_text,"]")]

            #if it's a function-related
            if string.find(varline, "FUNC")!=-1:
                varline = string.replace(varline, "FUNC ", "")
                self.func = True
                if string.find(varline, "(")!=-1:
                    self.funcArgument = varline[string.find(varline, "(")+1:string.find(varline, ")")]
                    varline = varline[0:string.find(varline, "(")]+varline[string.find(varline, ")")+1:]
                self.funcName = varline
            else:
                self.func = False

            #if it's about the bitfield
            if string.find(varline, "BIT")!=-1:
                varline = string.replace(varline, "BIT ", "")
                self.bit = True
            else:
                self.bit = False

            #getting variable name and tempVar
            if(string.find(varline, ' ')!=-1):
                varline = varline[0:string.find(varline," ")]
            self.variable = string.strip(varline,"~")

            if varline[0] == '~' :
                varline = varline[string.find(varline,'.'):]
                self.tempVar = "temp"+string.capitalize(varline[1])+varline[2:]

        #if it's a bitfield
        if self.bit==True:
            #whether bit should be written to 1 or to 0
            if string.find(_text, "|=")!=-1:
                self.bitInstall = True
            else:
                self.bitInstall = False

        #what costant is written here (for defines or enums)
        if string.find(_text, "[")!=-1 and string.find(_text, "=")!=-1:
            self.enum = string.strip(_text[string.find(_text, "=")+1:string.find(_text, "]")],"~ ")

        #getting the rest of the text (not variable or func related)
        if string.find(_text,"[")!=-1:
            _text = _text[0:string.find(_text,"[")]+_text[string.find(_text,"]")+1:]
        _text = string.strip(_text, " \t")

        self.text = _text
        self.child = _child
        self.parent = _parent
        self.next = _next
        self.previous = _prev
        self.name = _name
        self.number = _number

def GetLevel(line):
    return len(line)-len(string.lstrip(line, '-'))

def LookForChild(newlines, i):
    currLevel = GetLevel(newlines[i])
    for j in range(i+1, len(newlines)):
        level = GetLevel(newlines[j])
        if level>currLevel:
            return string.lstrip(newlines[j], '-')
        if level<currLevel or level==currLevel:
            return LookForParent(newlines,i)
    return LookForParent(newlines,i)

def LookForParent(newlines, i):
    currLevel = GetLevel(newlines[i])
    if currLevel==1:
        return string.lstrip(newlines[i], '-')
    for j in range(i-1, -1, -1):
        level = GetLevel(newlines[j])
        if level<currLevel:
            return string.lstrip(newlines[j], '-')

def LookForNext(newlines, i):
    currLevel = GetLevel(newlines[i])
    if currLevel==1:
        return string.lstrip(newlines[i], '-')

    #if it's the last element in input list
    if i==len(newlines)-1:
        parent = LookForParent(newlines,i)
        firstChild = newlines.index('-'*(currLevel-1)+parent)+1
        return string.lstrip(newlines[firstChild], '-')

    #from the next in input list to the end
    for j in range(i+1, len(newlines)):
        level = GetLevel(newlines[j])
        #if further is "upper"
        if level < currLevel:
            #looke for parent
            parent = LookForParent(newlines,i)
            #first parent's child is the next for current item
            firstChild = newlines.index('-'*(currLevel-1)+parent)+1
            return string.lstrip(newlines[firstChild], '-')
        if level == currLevel:
            return string.lstrip(newlines[j], '-')

    for j in range(0, len(newlines)):
        level = GetLevel(newlines[j])
        if level == currLevel:
            return string.lstrip(newlines[j], '-')

def LookForPrevious(newlines, i):
    currLevel = GetLevel(newlines[i])
    if i==0:
        return string.lstrip(newlines[0], '-')

    if i==1:
        for j in range(len(newlines)-1, 0, -1):
            level = GetLevel(newlines[j])
            if level == currLevel:
                return string.lstrip(newlines[j],'-')

    for j in range(i-1, 0, -1):
        level = GetLevel(newlines[j])
        if level < currLevel:
            for k in range(i, len(newlines)):
                level = GetLevel(newlines[k])
                if level < currLevel:
                    for l in range(k-1, 0, -1):
                        level = GetLevel(newlines[l])
                        if level==currLevel:
                            return string.lstrip(newlines[l], '-')
        if level == currLevel:
            return string.lstrip(newlines[j], '-')

def GenerateSettingsh(items):
    settingsh = open("settings.h", 'w')
    settingshLines = []
    parents = []
    #gathering all variables
    for item in items:
        if item.variable!="":
            parents.append(item.variable)
    parents = list(set(parents))

    enums = []
    #gathering all constants used for changing variables
    for parent in parents:
        txt = []
        for item in items:
            if item.variable == parent and len(item.enum)!=0 and not(item.enum.isdigit()):
               txt.append(item.enum)
        if len(txt)!=0:
            enums.append(EnumItem(parent,sorted(list(set(txt)))))

    for enum in enums:
        settingshLines.append("enum\n{\n\t")
        settingshLines.append(',\n\t'.join(enum.text))
        settingshLines.append("\n};\n\n")

    #check what structures do we have
    structs = []
    for item in items:
        if string.find(item.variable,".")!=-1:
            structs.append(item.variable[0:string.find(item.variable,'.')])
    structs = list(set(structs))

    #defining the number of possible values in a variable (to get the right type)
    for item in items:
        for pivot in items:
            if item.variable == pivot.variable and item.variable!="":
                item.valuesNum = item.valuesNum+1
        if item.bit == True:
            item.valuesNum = item.valuesNum/2

    vars = []
    for struct in structs:
        settingshLines.append("struct "+string.capitalize(struct)+"\n{\n")
        for item in items:
            if string.find(item.variable, ".")!=-1:
                type = ""
                #defining the approptiate variable type
                if item.bit == True:
                    if item.valuesNum <= 8:
                        type = "char"
                    if item.valuesNum > 8 and item.valuesNum <= 16:
                        type = "short"
                    if item.valuesNum > 16 and item.valuesNum <= 32:
                        type = "long"
                else:
                    if item.valuesNum < 255:
                        type = "char"
                    if item.valuesNum > 255:
                        type = "int"
                vars.append("\t"+type+" "+item.variable[string.find(item.variable,'.')+1:] +";\n")
        vars = list(set(vars))
        settingshLines = settingshLines+vars
        settingshLines.append("};\n")
    settingsh.writelines(settingshLines)
    settingsh.close()

def GenerateMenuc(items):
    menuc = open("menu.c", 'w')
    iteminsert = open("iteminsert.txt", 'r')
    menuclines = []
    txts = []
    i=0
    for item in items:
        txts.append(item.text)
        item.text = "mText["+str(i)+"]"
        i=i+1

	#definining arrays of items and their texts
    menuclines.append("struct Menu mItem[MENU_SIZE];\n")
    menuclines.append("unsigned char mText[MENU_SIZE][];\n")
    menuclines.append("\n")
    for line in iteminsert.readlines():
        menuclines.append(line)

    menuclines.append("\n\nvoid InitMenu()\n{\n")
    for i in range(len(items)):
        menuclines.append('\t'+items[i].text+' = "'+txts[i]+'";\n')
    menuclines.append('\n')
    #menu items initialization
    for item in items:
        l = [item.name, item.next, item.previous, item.parent, item.child, '0', item.text]
        cline = "\tItemInsert(" + ','.join(l)+");"
        menuclines.append(cline+"\n")
    menuclines.append("}\n")
    menuc.writelines(menuclines)
    menuc.close()

def GenerateMenuh(items):
    menuh = open("menu.h", 'w')
    menustruct = open("struct menu.txt", 'r')
    menuhLines = []

    #generate func arguments enums
    enums = []
    parents = []
    for item in items:
        if len(item.funcName)!=0:
            parents.append(item.funcName)
    parents = list(set(parents))

    for parent in parents:
        txt = []
        for item in items:
            if item.funcName == parent and not(item.funcArgument.isdigit()) and len(item.funcArgument)!=0:
                txt.append(item.funcArgument)

        if len(txt)!=0:
            enums.append(EnumItem(parent,sorted(list(set(txt)))))


    for enum in enums:
        menuhLines.append("enum\n{\n\t")
        menuhLines.append(',\n\t'.join(enum.text))
        menuhLines.append("\n};\n\n")

    menuhLines.append("#define MENU_SIZE "+str(len(items))+"\n")

    menuh.writelines(menuhLines)
    menuh.writelines(menustruct.readlines())
    menuh.close()
    menustruct.close()

#generating basic interrupt code
def GenerateInterrupts(lines, items):
    interruptsc = open("interrupts.c", "w")
    interruptscLines = []

    #decalre temp variables
    for item in items:
        if len(item.tempVar) !=0:
            interruptscLines.append("char "+item.tempVar+";\n")
        if len(item.variable)!=0 and string.find(item.variable, ".")==-1:
            interruptscLines.append("char "+item.variable+";\n")

    #generate interrupt handler for "EXIT" button
    interruptscLines.append("\n\nvoid InterruptExit()\n{\n")
    interruptscLines.append("\tcurrentMenuItem = mItem[currentMenuItem].Parent;\n}\n\n")

    #generate interrupt handler for "NEXT" button
    interruptscLines.append("void InterruptNext()\n{\n")
    for item in items:
        if item.bit==False and item.variable!="" and len(item.tempVar)!=0:
            interruptscLines.append("\tif(currentMenuItem == "+item.name+")\n\t{\n\t\t"+item.tempVar +'++;\n}\n')
    interruptscLines.append("\n\tcurrentMenuItem = mItem[currentMenuItem].Next;")
    interruptscLines.append("\n}\n\n")

    #generate interrupt handler for "PREVIOUS" button
    interruptscLines.append("void InterruptPrev()\n{\n")
    for item in items:
        if item.bit==False and item.variable!="" and len(item.tempVar)!=0:
            interruptscLines.append("\tif(currentMenuItem == "+item.name+")\n\t{\n\t\t"+item.tempVar +'--;\n')
    interruptscLines.append("\n\tcurrentMenuItem=mItem[currentMenuItem].Previous;")
    interruptscLines.append("\n}\n\n")

    #generate interrupt handler for "ENTER" button
    interruptscLines.append("void InterruptEnter()\n{\n")
    interruptscLines.append("\tswitch(currentMenuItem)\n\t{\n")
    for item in items:
        if item.variable!="":
            if item.bit == True:
                if item.bitInstall == True:
                    interruptscLines.append("\t\tcase "+item.name+":\n\t\t"+item.variable+" |= (1<<" + item.enum + ");\n")
                    interruptscLines.append("\t\tbreak;\n")
                if item.bitInstall == False:
                    interruptscLines.append("\t\tcase "+item.name+":\n\t\t"+item.variable+" &= ~(1<<" + item.enum + ");\n")
                    interruptscLines.append("\t\tbreak;\n")
            else:
                if item.enum != "":
                    interruptscLines.append("\t\tcase "+item.name+":\n\t\t"+item.variable+" = "+item.enum+";\n")
                    interruptscLines.append("\t\tbreak;\n")
            if len(item.tempVar)!=0:
                interruptscLines.append("\t\tcase "+item.name+":\n\t\t"+item.variable+" = "+item.tempVar+";\n")
                interruptscLines.append("\t\tbreak;\n")

    for item in items:
        if item.func == True:
            interruptscLines.append("\t\tcase "+item.name+":\n")
            interruptscLines.append('\t\t'+item.funcName+'('+item.funcArgument+');\n')
            interruptscLines.append('\t\tbreak;\n')
    interruptscLines.append("\tdefault:\n\t\tbreak;\n\t}\n")
    interruptscLines.append("\n\n\tcurrentMenuItem=mItem[currentMenuItem].Child;\n\n")

    for item in items:
        if len(item.tempVar)!=0:
            interruptscLines.append("\tif(currentMenuItem == "+item.name+")\n\t\t"+item.tempVar+" = "+item.variable+";\n")

    interruptscLines.append("}\n\n\t////////////////////////////////////////////\n\t//what to display when user enters this menu item\n")

    interruptscLines.append("\tswitch(currentMenuItem)\n\t{\n")
    for item in items:
        if len(item.variable)!=0 and len(item.tempVar)!=0:
            interruptscLines.append("\t\tcase "+item.name+":")
            interruptscLines.append('\n\t\t\tsprintf(displayBuffer[1], "-   %d   +", '+item.tempVar+');\n\t')
            interruptscLines.append("\t\tbreak;\n")
    interruptscLines.append("\t\tdefault:\n\t\t\tConvertChar(mItem[currentMenuItem].Text, displayBuffer[1]);\n\t\t\tbreak;\n\t}\n")
    interruptsc.writelines(interruptscLines)
    interruptsc.close()

def main():
    f = open("menu.txt", 'r')
    lines = f.readlines()
    newlines = []
    items = []

	#generating new names
    for i in range(len(lines)):
        name = str(i)
        currLevel = GetLevel(lines[i])
        newlines.append('-'*currLevel+name)

	#finding the dependencies and creating MenuItem instances
    for i in range(len(newlines)):
        next = LookForNext(newlines, i)
        prev = LookForPrevious(newlines, i)
        name = string.lstrip(newlines[i], '-')
        text = string.strip(lines[i], '-\n\r')
        child = LookForChild(newlines, i)
        parent = LookForParent(newlines, i)
        items.append(MenuItem(text, child, parent, next, prev, name, i))

    GenerateSettingsh(items)
    GenerateInterrupts(lines, items)
    GenerateMenuc(items)
    GenerateMenuh(items)

    f.close()

if __name__=="__main__":
    main()
    
