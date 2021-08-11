import os
import sys

import xlrd

from reg_rtl_template import *


class c_reg(object):
    def __init__(self, name, addr, default_val):
        self.name = name
        self.addr = int(addr, 16)
        self.field_list = []
        self.default_val = int(default_val, 16)

    def get_name(self):
        return self.name

    def get_addr(self):
        return self.addr

    def get_field_list(self):
        return self.field_list

    def get_default_val(self):
        return self.default_val

    def add_field(self, field_name, field_width, field_type,field_description):
        #print("adding field")
        #print(field_width)
        if re.search(r'\.', field_width):
            print("field_width type float @" + field_name + " : " + str(field_width) + "? convert to int\n")
            field_width = str(int(float(field_width)))
        if not isinstance(field_width, str):
            raise Exception("field_width type Error @" + field_name + ":" + str(field_width) + "\n")
        if not re.search(r':', field_width):
            self.field_list.append({"name": field_name, "width": 1, "begin_pos": int(field_width), "type": field_type, "description":field_description})
        else:
            end_pos, begin_pos = re.search(r'(\d+):(\d+)', field_width).group(1, 2)
            width = int(end_pos) - int(begin_pos) + 1
            self.field_list.append(
                {"name": field_name, "width": width, "begin_pos": int(begin_pos), "type": field_type , "description":field_description})

    def get_input_port(self):
        input_port_list = []
        for field in self.field_list:
            if re.search("RO", field["type"]):
                input_port_list.append((field["name"], field["width"]))
            elif re.search("RWCN", field["type"]):
                input_port_list.append((field["name"] + "_inc", 1))
                input_port_list.append((field["name"] + "_num", field["width"]))
            elif re.search("RWSC", field["type"]):
                input_port_list.append((field["name"] + "_clr", field["width"]))
            elif re.search("RWCI", field["type"]):
                input_port_list.append((field["name"] + "_inc", 1))
            elif re.search("RWC", field["type"]):
                input_port_list.append((field["name"] + "_set", field["width"]))
            elif re.search("RC", field["type"]):
                input_port_list.append((field["name"] + "_set", field["width"]))
        return input_port_list

    def get_output_port(self):
        output_port_list = []
        for field in self.field_list:
            if re.match("RW", field["type"]):
                output_port_list.append((field["name"], field["width"]))
            elif re.search("RWCC", field["type"]):
                output_port_list.append((field["name"], field["width"]))
            elif re.search("RWC", field["type"]):
                output_port_list.append((field["name"], field["width"]))
            elif re.search("RWSC", field["type"]):
                output_port_list.append((field["name"], field["width"]))
        return output_port_list

    def have_writable_field(self):
        result = False
        for field in self.field_list:
            result |= field["type"] in ["RW", "RWCN", "RWSC", "RWCI", "RWCC", "RWC"]
        return result

    def have_rc_field(self):
        result = False
        for field in self.field_list:
            result |= field["type"] in ["RC"]
        return result


def is_writable_field(type):
    return type in ["RW", "RWCN", "RWSC", "RWCI", "RWCC", "RWC"]


def sheet_proc(sheet):
    reg_list = []
    field_name_list = []
    field_width_list = []
    field_type_list = []
    field_description_list = []
    row_num = sheet.nrows
    col_num = sheet.ncols
    print("Cur Processing sheet %s row:%d col:%d" % (sheet.name, row_num, col_num))
    reg_main_name = ""
    reg_addr = ""
    default_val = ""
    for x in range(2, row_num):  # without title
        cell_list = sheet.row(x)
        # print(field_name_list)
        #print("---",cell_list)
        # print("^^^", cell_list[1].value)
        if(not re.search("~",cell_list[1].value)):
            if (cell_list[0].ctype != 0):  # Base
                # print("+++", cell_list)
                if (x != 2) and len(reg_main_name)>0:
                    reg_list.append(c_reg(reg_main_name, reg_addr, default_val))
                    for j in range(0, len(field_name_list)):
                        reg_list[-1].add_field(field_name_list[j], str(field_width_list[j]), field_type_list[j],field_description_list[j])
                    print(reg_list[-1].get_name())
                if len(field_name_list) > 0:
                    field_name_list = []
                    field_width_list = []
                    field_type_list = []
                    field_description_list = []
                reg_main_name = cell_list[0].value
                reg_addr = cell_list[1].value
                default_val = cell_list[2].value
            field_name = cell_list[3].value
            field_width = cell_list[4].value
            field_type = cell_list[5].value
            field_description = cell_list[6].value
            if field_name != "Reserved":
                # print("***", cell_list)

                field_name_list.append(field_name)
                field_width_list.append(field_width)
                field_type_list.append(field_type)
                field_description_list.append(field_description)
            if (x == row_num - 1):
                # if(cell_list[0].ctype != 0): # base
                reg_list.append(c_reg(reg_main_name, reg_addr, default_val))
                for j in range(0, len(field_name_list)):
                    reg_list[-1].add_field(field_name_list[j], str(field_width_list[j]), field_type_list[j],field_description_list[j])
    temp_list = []
    for reg_ins in reg_list:
        # print(reg_ins.get_name(), reg_ins.get_addr(), reg_ins.get_field_list())
        cur_addr = reg_ins.get_addr()
        if cur_addr in temp_list:
            raise Exception("ADDR DUPLICATE ERROR!:0x%x" % (cur_addr))
        else:
            temp_list.append(cur_addr)

    return reg_list


def file_proc_rtl(r_file):
    workbook = xlrd.open_workbook(r_file)
    for sheet in workbook.sheets():
        print(sheet.name)
        if (sheet.name != "DIO"):
            print("ERR", sheet.name)
            continue
        module_name = sheet.cell(0, 1).value.lower() + "_dio"
        bus_addr_width = int(sheet.cell(0, 3).value)
        reg_list = sheet_proc(sheet)
        file = open(module_name + ".v", "w")
        ### file head
        file_head_gen(file, module_name)
        file.write("module " + module_name + "(\n")
        ### ctrl Bus
        ctrl_bus_gen(file, bus_addr_width)

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
        file.write("wire [%d:0] PADDR_PAD = {PADDR,2'b0};\n" % (bus_addr_width - 1))
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
                                         field["type"], bus_addr_width, reg.get_name().lower())
            else:
                file.write("// no writable reg at this addr\n\n")

        gen_rc_reg(file, bus_addr_width, reg_list)
        file.write("\n\n")
        gen_read_reg(file, bus_addr_width, reg_list)

        file.write("\n\nendmodule")
        file.close()


def file_proc_uvm(r_file):
    workbook = xlrd.open_workbook(r_file)
    for sheet in workbook.sheets():
        print(sheet.name)
        if (sheet.name != "DIO"):
            print("ERR", sheet.name)
            continue
        module_name = sheet.cell(0, 1).value.lower()
        bus_addr_width = int(sheet.cell(0, 3).value)
        base_addr = int(sheet.cell(0, 5).value, 16)
        reg_list = sheet_proc(sheet)
        file = open(module_name + "_ral_model" + ".sv", "w")
        ### file head
        file_head_gen(file, module_name + "_ral_model")
        file.write("`ifndef %s\n" % ((module_name + "_ral_model").upper() + "__SV"))
        file.write("`define %s\n" % ((module_name + "_ral_model").upper() + "__SV"))
        for reg in reg_list:
            gen_ral_model(reg, file)
        file.write("class c_%s_reg_model extends uvm_reg_block;\n" % module_name)
        for reg in reg_list:
            file.write("    rand %s %s;\n" % ("reg_" + reg.get_name().lower(), reg.get_name().lower()))
        file.write("    virtual function void build();\n")
        addr_adj = hex(base_addr)
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
            addr_adj = str(bus_addr_width) + "'h" + addr_adj
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
        file.write("    `uvm_object_utils(c_%s_reg_model)\n" % module_name)
        file.write("    function new(input string name=\"c_%s_reg_model\");\n" % module_name)
        file.write("        super.new(name,UVM_NO_COVERAGE);\n")
        file.write("    endfunction\n")
        file.write("    function void reset(input string kind=\"HARD\");\n")
        file.write("        if (kind != \"SOFT\")\n")
        file.write("            super.reset(kind);\n")
        file.write("    endfunction\n")
        file.write("endclass\n")
        file.write("`endif\n")
        file.close()


def gen_ral_model(reg: c_reg, file):
    type_map = {}
    type_map["RC"] = "RC"
    type_map["RO"] = "RO"
    type_map["RW"] = "RW"
    type_map["RWCN"] = "W0C"
    type_map["RWSC"] = "W1C"
    type_map["RWCI"] = "W0C"
    type_map["RWC"] = "W0C"
    type_map["RWCC"] = "W1C"
    default_val = reg.get_default_val()
    file.write("class %s extends uvm_reg;\n" % ("reg_" + reg.get_name().lower()))
    for field in reg.get_field_list():
        name = field["name"]
        file.write("    rand uvm_reg_field %s;\n" % name)
    file.write("    virtual function void build();\n")
    for field in reg.get_field_list():
        name = field["name"]
        file.write("        %s = uvm_reg_field::type_id::create(\"%s\");\n" % (name, name))
    file.write("    endfunction;\n")
    file.write("    `uvm_object_utils(%s)\n" % ("reg_" + reg.get_name().lower()))
    file.write("    function new(input string name=\"%s\");\n" % ("reg_" + reg.get_name().lower()))
    file.write("        super.new(name,32,UVM_NO_COVERAGE);\n")
    file.write("    endfunction\n")
    file.write("endclass\n\n")


def file_proc_json(r_file):
    workbook = xlrd.open_workbook(r_file)
    for sheet in workbook.sheets():
        print(sheet.name)
        if (sheet.name != "DIO"):
            print("ERR", sheet.name)
            continue
        module_name = sheet.cell(0, 1).value.lower() + "_dio"
        bus_addr_width = str(int(sheet.cell(0, 3).value))
        base_addr = int(sheet.cell(0, 5).value, 16)
        reg_list = sheet_proc(sheet)
        file = open(module_name + ".json", "w")
        file.write("{\n")
        file.write("\t\"moduleName\":\"" + module_name + "\",\n")
        file.write("\t\"addrWidth\":" + bus_addr_width + ",\n")
        file.write("\t\"baseAddr\":" + str(base_addr) + ",\n")
        file.write("\t\"Regs\":[\n")
        reg_list_len = len(reg_list)
        reg_cnt = 1
        for reg in reg_list:
            file.write("\t\t{\n")
            file.write("\t\t\"name\":\"" + reg.get_name() + "\",\n")
            file.write("\t\t\"addr\":\"%s\",\n" % hex(reg.get_addr()))
            file.write("\t\t\"defaultValue\":\"%s\",\n" % hex(reg.get_default_val()))
            file.write("\t\t\"fields\":[\n")
            field_list_len = len(reg.get_field_list())
            field_cnt = 1
            for field in reg.get_field_list():
                last_coma = "" if field_cnt == field_list_len else ","
                field_cnt += 1
                (name, width, begin_pos, type,description) = (field["name"], field["width"], field["begin_pos"], field["type"] , field["description"])
                file.write(
                    "\t\t\t{\"fieldName\":\"%s\",\"width\":%s,\"fieldLsb\":\"%s\",\"type\":\"%s\",\"description\":\"%s\"}%s\n"
                    % (name, width, begin_pos, type, description, last_coma))
            file.write("\t\t\t]\n")
            last_coma = "" if reg_cnt == reg_list_len else ","
            file.write("\t\t}%s\n" % last_coma)
            reg_cnt += 1
        file.write("\t]\n")
        file.write("}\n")
        file.close()


if __name__ == '__main__':
    for file in sys.argv[1:len(sys.argv)-1]:
        if not os.path.exists(file):
            sys.exit("ERROR! file: %s do not exist!" % file)
        if not os.path.isfile(file):
            sys.exit("ERROR! file: %s is not a file!" % file)

        if (sys.argv[-1] == "xls2rtl"):
            file_proc_rtl(file)
        elif (sys.argv[-1] == "xls2ral"):
            file_proc_uvm(file)
        elif (sys.argv[-1] == "xls2json"):
            file_proc_json(file)
        else:
            sys.exit("Error Function Input!")

