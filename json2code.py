import json
import os
import sys
import re
from excel_convert import file_head_gen
from excel_convert import c_reg
from excel_convert import ctrl_bus_gen
from excel_convert import port_str
from excel_convert import is_writable_field
from excel_convert import gen_writable_reg
from excel_convert import gen_rc_reg
from excel_convert import gen_read_reg
from excel_convert import gen_ral_model

def jsonLoad(r_file):
    with open(r_file, 'r') as f:
        jsonData = json.load(f)
    return jsonData


def buildRegClass(jsonData):
    reg_list = []
    for reg in jsonData["Regs"]:
        #print(reg["name"])
        reg_list.append(c_reg(reg["name"], reg["addr"], reg["defaultValue"]))
        for field in reg["fields"]:
            #print(field["fieldName"])
            if field["width"] == 1:
                pos_str = str(field["fieldLsb"])
            else:
                msbPos = int(field["width"]) + int(field["fieldLsb"]) - 1
                pos_str = (str(msbPos) + ":" + str(field["fieldLsb"]))
            #if not re.search(r':', pos_str):
                #print("with : width")
            #print(type(pos_str))
            reg_list[-1].add_field(field["fieldName"],
                                   str(pos_str),
                                   field["type"],
                                   field["description"])

    return (jsonData["moduleName"], jsonData["addrWidth"],jsonData["baseAddr"], reg_list)


def outputRtl(moduleName, addrWidth, reg_list):
    file = open(moduleName + ".v", "w")
    ### file head
    file_head_gen(file, moduleName)
    file.write("module " + moduleName + "(\n")
    ### ctrl Bus
    ctrl_bus_gen(file, addrWidth)
    ### ports
    file.write("// input signals\n")
    for reg in reg_list:
        for name, width in reg.get_input_port():
            file.write(port_str(name, "input", width))
    file.write("// output signals\n")
    temp_str = ""
    for reg in reg_list:
        for name, width in reg.get_output_port():
            temp_str = temp_str + port_str(name, "output", width)
        temp_str = re.sub(",\s+$", "\n", temp_str)
        file.write(temp_str)
        file.write(");\n")
        file.write("genvar i;\n")
        ### ports fin
        file.write("// inner ctrl signals\n")
        file.write("wire [%d:0] PADDR_PAD = {PADDR,2'b0};\n" % (addrWidth - 1))
        file.write("wire registers_wr = PSEL & PENABLE & PWRITE;\n")
        file.write("wire registers_rd = PSEL & (~PWRITE);\n")

        for reg in reg_list:
            file.write("// writable registers @ %4s \n" % hex(reg.get_addr()))
            if reg.have_writable_field():
                dval_temp = reg.get_default_val()
                dval_temp = hex(dval_temp)
                dval_temp = re.sub("0x", "", dval_temp)
                dval_temp = dval_temp.rjust(4, '0')
                dval_temp = "32" + "'h" + dval_temp
                file.write("wire [31:0] %s = %s;" % (reg.get_name().lower() + "_dval", dval_temp))
                for field in reg.get_field_list():
                    if is_writable_field(field["type"]):
                        gen_writable_reg(file, field["name"], reg.get_addr(), field["width"], field["begin_pos"],
                                         field["type"], addrWidth, reg.get_name().lower())
            else:
                file.write("// no writable reg at this addr\n\n")

    gen_rc_reg(file, addrWidth, reg_list)
    file.write("\n\n")
    gen_read_reg(file, addrWidth, reg_list)

    file.write("\n\nendmodule")
    print("RTL gene done!")
    file.close()


def outputRal(moduleName, addrWidth, baseAddr,reg_list):
    file = open(moduleName + "_ral_model" + ".sv", "w")
    ### file head
    file_head_gen(file, moduleName + "_ral_model")
    file.write("`ifndef %s\n" % ((moduleName + "_ral_model").upper() + "__SV"))
    file.write("`define %s\n" % ((moduleName + "_ral_model").upper() + "__SV"))
    for reg in reg_list:
        gen_ral_model(reg, file)
    file.write("class c_%s_reg_model extends uvm_reg_block;\n" % moduleName)
    for reg in reg_list:
        file.write("    rand %s %s;\n" % ("reg_" + reg.get_name().lower(), reg.get_name().lower()))
    file.write("    virtual function void build();\n")
    addr_adj = hex(baseAddr)
    addr_adj = re.sub("0x", "", addr_adj)
    addr_adj = addr_adj.rjust(4, '0')
    addr_adj = "32'h" + addr_adj
    file.write("        default_map = create_map(\"default_map\",%s,4,UVM_LITTLE_ENDIAN,0);\n" % addr_adj)
    type_map = {}
    type_map["RC"] = "RC"
    type_map["RO"] = "RO"
    type_map["RW"] = "RW"
    type_map["RWCN"] = "W0C"
    type_map["RWSC"] = "W1C"
    type_map["RWCI"] = "W0C"
    type_map["RWC"] = "W0C"
    type_map["RWCC"] = "W1C"
    for reg in reg_list:
        default_val = reg.get_default_val()
        addr_adj = hex(reg.get_addr())
        addr_adj = re.sub("0x", "", addr_adj)
        addr_adj = addr_adj.rjust(4, '0')
        addr_adj = str(addrWidth) + "'h" + addr_adj
        file.write("        %s = %s::type_id::create(\"%s\",,get_full_name());\n" % (
            reg.get_name().lower(), "reg_" + reg.get_name().lower(), reg.get_name().lower()))
        file.write("        %s.configure(this,null,"");\n" % (reg.get_name().lower()))
        file.write("        %s.build();\n" % reg.get_name().lower())
        for field in reg.get_field_list():
            (name, width, begin_pos, type) = (field["name"], field["width"], field["begin_pos"], field["type"])
            mask = 0xFFFF_FFFF
            mask = mask >> (32 - width)
            field_default_val = default_val >> begin_pos
            field_default_val = field_default_val & mask
            field_default_val = hex(field_default_val)
            field_default_val = re.sub("0x", "", field_default_val)
            field_default_val = str(width) + "'h" + field_default_val
            file.write("            %s.%s.configure(%s,%d,%d,\"%s\",1,%s,1,0,1);\n" % (
                reg.get_name().lower(), name, reg.get_name().lower(), width, begin_pos, type_map[type],
                field_default_val))
            file.write("            %s.add_hdl_path_slice(\"%s\",%d,%d);\n" % (
                reg.get_name().lower(), name, begin_pos, width))
        file.write("        default_map.add_reg(%s,%s,\"RW\");\n" % (reg.get_name().lower(), addr_adj))
    file.write("    endfunction\n")
    file.write("    `uvm_object_utils(c_%s_reg_model)\n" % moduleName)
    file.write("    function new(input string name=\"c_%s_reg_model\");\n" % moduleName)
    file.write("        super.new(name,UVM_NO_COVERAGE);\n")
    file.write("    endfunction\n")
    file.write("    function void reset(input string kind=\"HARD\");\n")
    file.write("        if (kind != \"SOFT\")\n")
    file.write("            super.reset(kind);\n")
    file.write("    endfunction\n")
    file.write("endclass\n")
    file.write("`endif\n")
    file.close()


if __name__ == '__main__':
    for file in sys.argv[1:len(sys.argv)-1]:
        if not os.path.exists(file):
            sys.exit("ERROR! file: %s do not exist!" % file)
        if not os.path.isfile(file):
            sys.exit("ERROR! file: %s is not a file!" % file)

        (moduleName, addrWidth,baseAddr, reg_list) = buildRegClass(jsonLoad(file))
        if (sys.argv[-1] == "json2rtl"):
            outputRtl(moduleName, addrWidth, reg_list)
        elif (sys.argv[-1] == "json2ral"):
            outputRal(moduleName, addrWidth, baseAddr, reg_list)
        else:
            sys.exit("Error Function Input!")
