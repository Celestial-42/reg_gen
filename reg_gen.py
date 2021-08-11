from excel_convert import *
from json2code import *
from json2docx import *
import os

def main():
    if (len(sys.argv) <= 1):
        print("usage : reg_gen.py file function")
        print("function:")
        print("    xls2rtl    Excel to RTL")
        print("    xls2ral    Excel to ral_model")
        print("    xls2json   Excel to json")
        print("    json2rtl   json to RTL")
        print("    json2ral   json to ral_model")
        print("    json2excel json to excel(TBD)")
        print("    json2docx  json to docx&pdf")
        sys.exit("ERROR! No input File!")
    else:
        for file in sys.argv[1:len(sys.argv)-1]:
            if not os.path.exists(file):
                sys.exit("ERROR! file: %s do not exist!" % file)
            if not os.path.isfile(file):
                sys.exit("ERROR! file: %s is not a file!" % file)

            if(sys.argv[-1] == "xls2rtl"):
                file_proc_rtl(file)
            elif (sys.argv[-1] == "xls2ral"):
                file_proc_uvm(file)
            elif (sys.argv[-1] == "xls2json"):
                file_proc_json(file)
            elif (sys.argv[-1] == "json2rtl"):
                (moduleName, addrWidth, baseAddr, reg_list) = buildRegClass(jsonLoad(file))
                outputRtl(moduleName, addrWidth, reg_list)
                print("json2rtl convert done!")
            elif (sys.argv[-1] == "json2ral"):
                (moduleName, addrWidth, baseAddr, reg_list) = buildRegClass(jsonLoad(file))
                outputRal(moduleName, addrWidth, baseAddr, reg_list)
                print("json2ral convert done!")
            elif (sys.argv[-1] == "json2docx"):
                (moduleName, addrWidth, baseAddr, reg_list) = buildRegClass(jsonLoad(file))
                outputDocx(moduleName, addrWidth, baseAddr, reg_list)
                outputPDF(moduleName)
                print("json2docx&pdf convert done!")
            else:
                sys.exit("Error Function Input!")

if __name__ == '__main__':
    main()
