import re

def file_head_gen(file,module_name):
    file.write("`timescale 1ns / 1ns"+"\n")
    file.write("//////////////////////////////////////////////////////////////////////////////////"+"\n")
    file.write("// Company       : Orbbec"+"\n")
    file.write("// Engineer      : "+"\n")
    file.write("// "+"\n")
    file.write("// Create Date   : "+"\n")
    file.write("// Design Name   : "+"\n")
    file.write("// Module Name   : %s\n" % module_name.upper())
    file.write("// Project Name  : "+"\n")
    file.write("// Target Devices: "+"\n")
    file.write("// Tool Versions : "+"\n")
    file.write("// Description   : "+"\n")
    file.write("// "+"\n")
    file.write("// Dependencies  : "+"\n")
    file.write("// "+"\n")
    file.write("// Revision      :"+"\n")
    file.write("// Revision -1.01 - File Created"+"\n")
    file.write("// Additional Comments:"+"\n")
    file.write("// "+"\n")
    file.write("//////////////////////////////////////////////////////////////////////////////////"+"\n")

def ctrl_bus_gen(file,bus_addr_width):
    file.write("//APB BUS\n")
    file.write("    input                       apb_clk,\n")
    file.write("    input                       apb_rstn,\n")
    file.write("    input                       statistic_clr,\n")
    file.write("    input                       PENABLE,\n")
    file.write("    input                       PSEL,\n")
    file.write("    input       [%2d: 0]         PADDR,\n" % (bus_addr_width-3))
    file.write("    input                       PWRITE,\n")
    file.write("    input       [31: 0]         PWDATA,\n")
    file.write("    output  reg [31: 0]         PRDATA,\n")

def port_str(name,direction,width):
    if(width ==1):
        width_mod = "\t\t"
    else:
        width_mod = "[{0:>2}:0]\t".format(width-1)
    if direction =="input":
        return "\tinput\t\t\t%s         %-20s,\n" % (width_mod,name)
    else:
        return "\toutput reg\t\t%s         %-20s,\n" % (width_mod,name)


def gen_writable_reg(file,name,addr,width,begin_pos,type,bus_addr_width,dval_name):
    if width > 1:
        pos_str = "[%-2d:%2d]" % (width+begin_pos-1,begin_pos)
    else:
        pos_str = "[%d]" % begin_pos
    addr_adj = hex(addr)
    addr_adj = re.sub("0x","",addr_adj)
    addr_adj = addr_adj.rjust(4,'0')
    addr_adj = str(bus_addr_width)+"'h"+ addr_adj
    file.write("// %s reg \n" % type)
    if type == "RW":
        file.write("always @(posedge apb_clk or negedge apb_rstn) begin\n")
        file.write("    if(!apb_rstn)\n")
        file.write("        %s <= %s%s;\n" % (name,dval_name+"_dval",pos_str))
        file.write("    else if(registers_wr & (PADDR_PAD[%d:0] == %s))\n" %(bus_addr_width-1,addr_adj))
        file.write("        %s <= PWDATA%s;\n" % (name,pos_str))
        file.write("end\n\n")

    if type == "RWC":
        if(width > 1) :
            file.write("generate\n")
            # file.write("genvar i;\n")
            file.write("for(i=0;i<%d;i=i+1) begin\n" % width)
            file.write("always @(posedge apb_clk or negedge apb_rstn) begin\n")
            file.write("    if(!apb_rstn)\n")
            file.write("        %s[i] <= %s[%s+i];\n" % (name, dval_name+"_dval", begin_pos))
            file.write("    else if(%s[i])\n" % (name+"_set"))
            file.write("        %s[i] <= 1'b1;\n" % name)
            file.write("    else if(registers_wr & (PADDR_PAD[%d:0] == %s))\n" %(bus_addr_width-1,addr_adj))
            file.write("        %s[i] <= %s[i] & PWDATA[%s+i];\n" % (name,name,begin_pos))
            file.write("end\n")
            file.write("end\n")
            file.write("endgenerate\n\n")
        else:
            file.write("always @(posedge apb_clk or negedge apb_rstn) begin\n")
            file.write("    if(!apb_rstn)\n")
            file.write("        %s <= %s%s;\n" % (name, dval_name+"_dval", pos_str))
            file.write("    else if(%s)\n" % (name+"_set"))
            file.write("        %s <= 1'b1;\n" % name)
            file.write("    else if(registers_wr & (PADDR_PAD[%d:0] == %s))\n" %(bus_addr_width-1,addr_adj))
            file.write("        %s <= %s & PWDATA%s;\n" % (name,name,pos_str))
            file.write("end\n\n")

    if type == "RWCC":
        if(width > 1) :
            file.write("generate\n")
            # file.write("genvar i;\n")
            file.write("for(i=0;i<%d;i=i+1) begin\n" % width)
            file.write("always @(posedge apb_clk or negedge apb_rstn) begin\n")
            file.write("    if(!apb_rstn)\n")
            file.write("        %s[i] <= %s[%s+i];\n" % (name, dval_name+"_dval", begin_pos))
            file.write("    else if(%s[i])\n" % (name+"_set"))
            file.write("        %s[i] <= 1'b1;\n" % name)
            file.write("    else if(registers_wr & (PADDR_PAD[%d:0] == %s))\n" %(bus_addr_width-1,addr_adj))
            file.write("        %s[i] <= %s[i] & (~PWDATA[%s+i]);\n" % (name,name,begin_pos))
            file.write("end\n")
            file.write("end\n")
            file.write("endgenerate\n\n")
        else:
            file.write("always @(posedge apb_clk or negedge apb_rstn) begin\n")
            file.write("    if(!apb_rstn)\n")
            file.write("        %s <= %s%s;\n" % (name, dval_name+"_dval", pos_str))
            file.write("    else if(%s)\n" % (name+"_set"))
            file.write("        %s <= 1'b1;\n" % name)
            file.write("    else if(registers_wr & (PADDR_PAD[%d:0] == %s))\n" %(bus_addr_width-1,addr_adj))
            file.write("        %s <= %s & (~PWDATA%s);\n" % (name,name,pos_str))
            file.write("end\n\n")

    if type == "RWCI":
       file.write("always @(posedge apb_clk or negedge apb_rstn) begin\n")
       file.write("    if(!apb_rstn)\n")
       file.write("        %s <= %s%s;\n" % (name, dval_name+"_dval", pos_str))
       file.write("    else if (statistic_clr) \n")
       file.write("        %s <= %d'b0;\n" % (name,width))
       file.write("    else if (registers_wr & (PADDR_PAD[%d:0] == %s)) begin\n" %(bus_addr_width-1,addr_adj))
       file.write("        if(PWDATA%s == %d'b0) begin\n" % (pos_str,width))
       file.write("            %s <= %s ? %d'd1 : %d'b0;\n" % (name,name+"_inc",width,width))
       file.write("        end\n")
       file.write("    end\n")
       file.write("    else if (%s) begin\n" % (name+"_inc"))
       file.write("        %s <= %s + %d'd1;\n" % (name,name,width))
       file.write("    end\n")
       file.write("end\n\n")

    if type == "RWCN":
       file.write("always @(posedge apb_clk or negedge apb_rstn) begin\n")
       file.write("    if(!apb_rstn)\n")
       file.write("        %s <= %s%s;\n" % (name, dval_name+"_dval", pos_str))
       file.write("    else if (statistic_clr) \n")
       file.write("        %s <= %d'b0;\n" % (name,width))
       file.write("    else if (registers_wr & (PADDR_PAD[%d:0] == %s)) begin\n" %(bus_addr_width-1,addr_adj))
       file.write("        if(PWDATA%s == %d'b0) begin\n" % (pos_str,width))
       file.write("            if(%s) \n" % (name+"_inc"))
       file.write("                %s <= %s;\n" % (name,name+"_num"))
       file.write("            else\n")
       file.write("                %s <= %d'b0;\n" % (name,width))
       file.write("        end\n")
       file.write("    end\n")
       file.write("    else if (%s) \n" % (name+"_inc"))
       file.write("        %s <= %s + %s;\n" % (name,name,name+"_num"))
       file.write("end\n\n")

    if type == "RWSC":
        if(width > 1) :
            file.write("generate\n")
            # file.write("genvar i;\n")
            file.write("for(i=0;i<%d;i=i+1) begin\n" % width)
            file.write("always @(posedge apb_clk or negedge apb_rstn) begin\n")
            file.write("    if(!apb_rstn)\n")
            file.write("        %s <= %s%s;\n" % (name, dval_name+"_dval", pos_str))
            file.write("    else if(%s[i])\n" % (name+"_clr"))
            file.write("        %s[i] <= 1'b0;\n" % name)
            file.write("    else if(registers_wr & (PADDR_PAD[%d:0] == %s))\n" %(bus_addr_width-1,addr_adj))
            file.write("        %s[i] <= PWDATA[%s+i];\n" % (name,begin_pos))
            file.write("end\n")
            file.write("end\n")
            file.write("endgenerate\n\n")
        else:
            file.write("always @(posedge apb_clk or negedge apb_rstn) begin\n")
            file.write("    if(!apb_rstn)\n")
            file.write("        %s <= %s[%s];\n" % (name, dval_name+"_dval", begin_pos))
            file.write("    else if(%s)\n" % (name+"_clr"))
            file.write("        %s <= 1'b0;\n" % name)
            file.write("    else if(registers_wr & (PADDR_PAD[%d:0] == %s))\n" %(bus_addr_width-1,addr_adj))
            file.write("        %s <= PWDATA%s;\n" % (name,pos_str))
            file.write("end\n\n")

def reg_at_addr_str(addr,field_list):
    str = ""
    cur_pos = 32
    addr_adj = hex(addr)
    addr_adj = re.sub("0x","",addr_adj)
    addr_adj = addr_adj.rjust(4,'0')
    sorted(field_list,key=lambda field: field["begin_pos"],reverse=True)
    for field in field_list:
        field_pos = int(field["begin_pos"]) + int(field["width"])
        if field_pos < cur_pos :
            str = str + "%d'b0," % (cur_pos - field_pos)
            cur_pos = field_pos
        str = str + field["name"] + ","
        cur_pos = cur_pos - int(field["width"])
    str = "wire [31:0] reg_at_%s = {%s};\n" % (addr_adj,re.sub(",$","",str))

    return str

def gen_rc_reg(file,bus_addr_width,reg_list):
    for reg in reg_list:
        if(reg.have_rc_field()):
            file.write("// rc registers @ %4s \n" % hex(reg.get_addr()))
            addr = reg.get_addr()
            addr_adj = hex(addr)
            addr_adj = re.sub("0x","",addr_adj)
            addr_adj = addr_adj.rjust(4,'0')
            addr_adj = str(bus_addr_width)+"'h"+ addr_adj
            for field in reg.get_field_list():
                if re.match("RC",field["type"]):
                    (name,width,begin_pos) = (field["name"],field["width"],field["begin_pos"])
                    if(field["width"] > 1) :
                        file.write("reg [%d:0] %s;\n" % (width-1,name))
                        file.write("generate\n")
                        # file.write("genvar i;\n")
                        file.write("for(i=0;i<%d;i=i+1) begin\n" % width)
                        file.write("always @(posedge apb_clk or negedge apb_rstn) begin\n")
                        file.write("    if(!apb_rstn)\n")
                        file.write("        %s[i] <= %s[i];\n" % (name,reg.get_name().lower()+"_dval"))
                        file.write("    else if(%s[i])\n" % (name+"_set"))
                        file.write("        %s[i] <= 1'b1;\n" % name)
                        file.write("    else if(registers_rd & (PADDR_PAD[%d:0] == %s))\n" %(bus_addr_width-1,addr_adj))
                        file.write("        %s[i] <= 1'b0;\n" % (name))
                        file.write("end\n")
                        file.write("end\n")
                        file.write("endgenerate\n\n")
                    else:
                        file.write("reg %s;\n" % name)
                        file.write("always @(posedge apb_clk or negedge apb_rstn) begin\n")
                        file.write("    if(!apb_rstn)\n")
                        file.write("        %s <= %s[%d];\n" % (name,reg.get_name().lower()+"_dval",begin_pos))
                        file.write("    else if(%s)\n" % (name+"_set"))
                        file.write("        %s <= 1'b1;\n" % name)
                        file.write("    else if(registers_rd& (PADDR_PAD[%d:0] == %s))\n" %(bus_addr_width-1,addr_adj))
                        file.write("        %s <= 1'b0;\n" % (name))
                        file.write("end\n\n")
        #else:
        #    file.write("// no rc reg at this addr\n\n")
    for reg in reg_list:
        file.write(reg_at_addr_str(reg.get_addr(),reg.get_field_list()))

def gen_read_reg(file,bus_addr_width,reg_list):
    file.write("always @(posedge apb_clk or negedge apb_rstn) begin\n")
    file.write("    if(!apb_rstn)\n")
    file.write("        PRDATA <= 32'b0;\n")
    file.write("    else if(registers_rd) begin\n")
    file.write("        case(PADDR_PAD[%d:0])\n" % (bus_addr_width-1))
    for reg in reg_list:
        addr_adj = hex(reg.get_addr())
        addr_adj = re.sub("0x","",addr_adj)
        addr_adj1 = addr_adj.rjust(4,'0')
        addr_adj2 = str(bus_addr_width)+"'h"+ addr_adj1
        file.write("            %s: PRDATA <= reg_at_%s;\n" % (addr_adj2,addr_adj1))
    file.write("            default : PRDATA <= 32'b0;\n")
    file.write("        endcase\n")
    file.write("    end\n")
    file.write("end\n\n")
