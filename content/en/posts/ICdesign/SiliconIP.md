---
title: 'Digital Circuits: Using IP'
date: 2025-08-14
categories:
- ICdesign
tags:
- ICdesign
series: null
images:
- /images/ICdesign/HardwareIP.png
AITranslated: true
---
The story goes like this: In the massive hardware industry, no single company can independently create a chip. Even Tier-1 companies like Nvidia and AMD have many designs that come from licensed IP (Intellectual Property).
Modern chips are like building blocks of IP, where each block may represent the hard work and dedication of countless engineers, along with the substantial investment in verification and optimization.

If you want to license your design to others, you certainly can't just offer up the RTL code for free. Otherwise, the buyer could directly look at your code, understand the concept, and implement it themselves.
Protecting hardware intellectual property rights is so important that IEEE even has a standard [IEEE 1735](https://standards.ieee.org/ieee/1735/7237/) to address this issue. All major EDA (Electronic Design Automation) vendors have tools that support IEEE 1735; the latest version is the second edition, released in 2023.

The operating principle behind it can be briefly summarized as follows:
1. Each EDA vendor, if following the IEEE1735 standard, will retain a private key and publicly publish the corresponding public key.
2. When providing IP, the IP vendor applies for the public key from the EDA vendor or uses the published public key to encrypt an AES key.
3. Encrypt the entire file with the AES key and send it to the IP user.

When the IP user opens the encrypted file with EDA software, the software can decrypt the AES key encrypted by the public key because it carries the private keys of various vendors. Once the AES key is obtained, the file can be decrypted. Without the private key, others cannot derive the AES key, thus achieving the protection of the implementation.

Putting theory aside, the mainstream examples currently use the RSA public key cryptosystem combined with the AES-128-CBC mode, and there have been incidents of [security vulnerabilities](https://www.ithome.com.tw/news/118076). Of course, this is not the fault of the vendors, as the private key, once written into the software, must be located somewhere. At worst, it can almost certainly be retrieved from memory. To effectively mitigate this issue, obtaining a key from the vendor via the network during decryption may be the only solution, but this would prevent offline execution.

Currently, this vulnerability is not considered too severe, but I believe the reliance is more on industry norms rather than encryption. Encryption might add some resistance but isn’t foolproof.
Certainly, you can break the private key to crack the IP you've paid dearly for, but what then?
Will you release it online without charge? That would be using my money for charity, wouldn’t it?
Will you secretly license it privately? If you bought something from someone and started licensing the same thing after some time, the IP seller is sure to report you… After that, the whole industry will know you are violating intellectual property rights, so who would dare give you anything to use?

# Three Levels of IP

As described in this reference document [What is the difference between soft macro and hard macro?](https://asic-soc.blogspot.com/2007/11/what-is-difference-between-soft-macro.html), in the hardware industry, IP is roughly divided into three types based on its position in the overall process: Soft Macro, Firm Macro, and Hard Macro ~~I only learned about this while writing this article~~. This paper attacking IEEE 1735 [How Not to Protect Your IP – An Industry-Wide Break of IEEE 1735 Implementations](https://arxiv.org/abs/2112.04838) contains a relevant diagram:

![DifferentIP](/images/ICdesign/HardwareIP.png)

In brief, Soft -> Firm -> Hard binds increasingly closely to the actual hardware. Soft IP is still source code; Firm IP has been converted to a Netlist; Hard IP is already at the Layout level.

## Soft Macro

Soft Macro provides a synthesizable RTL implementation that can be used on both FPGAs and as ASICs. However, Soft Macro also has corresponding drawbacks. Because the Design Constraint is set during synthesis, the process technology used by consumers may not be what you envisioned during design. For example, the designer might have used an excellent library capable of achieving a 100 MHz timing, but the buyer’s process and library might not support certain critical operations, ultimately synthesizing only to 75 MHz. These uncertainties are inherent in Soft Macro, so final PPA (Performance, Power, Area) and other parameters need careful examination.

When delivering Soft Macro, encryption is a must. The only exception I've heard of is ARM's licensing. If you pay enough, they will give you ARM's source code. They're not afraid of you copying it—without testing and patent protection, there's not much you can do with it.

## Firm Macro

Firm Macro refers to the gate-level netlist (connection list/netlist) obtained after RTL synthesis. During synthesis, the process technology must be determined, so Firm Macro is already tied to the process technology.

The advantage is that Firm Macro is optimized for Performance/Power/Area. Unlike Soft Macro, where the buyer is responsible for front-end synthesis and might inadvertently tamper with Design Constraint, leading to unforeseen circuits. At the gate-level, there is less concern about leaks because it’s harder to revert from gate-level to RTL.

I’ve been puzzled here about why there isn’t a more generic process that provides some common components. Just don’t worry about timing initially and first turn the design into a level of netlist that cannot be reverted to the original RTL. Once the process is decided, convert from this generic process to the actual process, using real components for timing, power, and area optimization. But this hasn't been achieved over the years, so there must be some limitations.

## Hard Macro

At the Hard Macro level, what is provided is an implementation highly tied to IC manufacturing. The Hard Macro that most people will encounter includes memory and chip pads. Taking memory as an example, what you will likely get includes:
* Verilog file of the behavior model for simulation use.
* Packaged .lib file or .db file that lets you add this black box during synthesis. The .db file will include timing data for the Design Compiler to complete timing simulation.
* [LEF](https://en.wikipedia.org/wiki/Library_Exchange_Format) file, describing the pin positions of this IP and how the power is connected?
* GDSII, in layout, we only use LEF to let the Layout software complete the Layout based on the shape. Before sending to the wafer factory, import GDS to replace the position specified by LEF to complete the layout.

Hard Macro has completed the layout, and from the outside, it looks like a black box. Besides Performance/Power/Area, pin definitions and timing should also be noted. You can only modify the position and direction during layout. At this Hard Macro level, there is generally no need to consider encryption issues unless the user wishes to watch the layout and try to restore the logic gates and transistors, like 6502 CPU's few thousand logic gates, but that should still be achievable.

# Encryption Methods of Various Software

Different EDA companies have different ways to encrypt IP. When it comes to IEEE1735 as a public standard, everyone will support it, and some companies, such as Synopsys, will also create their own encryption.

Here is a list I found, with subsections for the ones I've used:
* Synopsys VCS Only
* Synopsys Design Compiler Only
* Xilinx Vivado
* Cadence Xcelium
* Synopsys VCS
* Mentor Graphics Questa

Below I will add to it as I use them:

## Synopsys VCS Only

Refer to the previous [VCS article]({{< relref "vcs#使用-vcs-加密" >}}), encryption can be completed using the autoprotect option, and files encrypted can only be used for simulation with VCS, not for synthesis or with other vendors.

## Synopsys Design Compiler Only

The command is synenc, typically included with the purchase of the design compiler and straightforward to use.
```
synenc *.v *.vp
```
Once encrypted, only the design compiler can read the files, immediately converting them into the design compiler’s intermediate format, making it impossible to revert to the original RTL code. You cannot use it for simulation or share it with other vendors.

## Xilinx Vivado

Xilinx FPGA’s synthesis software lets you synthesize RTL to an FPGA. It implements [IEEE1735 support](https://www.amd.com/en/products/adaptive-socs-and-fpgas/intellectual-property/ip-encryption.html).
A standard Vivado license does not include IEEE1735 encryption functionality. For encryption functionality, please submit a request to xilinx_security_app@amd.com, and only the paid standard version grants access to this feature.

Since this is IEEE1735, first locate the public key in the Vivado installation directory – the path is:
```txt
/Vivado/<version>/data/pubkey
```

Then prepare keyfile.txt:

```verilog
`pragma protect version = 2
`pragma protect encrypt_agent = "XILINX"
`pragma protect encrypt_agent_info = "Xilinx Encryption Tool 2022"
`pragma protect begin_commonblock
`pragma protect control error_handling = "delegated"
`pragma protect control runtime_visibility = "delegated"
`pragma protect control child_visibility = "delegated"
`pragma protect control decryption=(activity==simulation) ? "false" : "true"
`pragma protect end_commonblock

`pragma protect begin_toolblock
`pragma protect rights_digest_method="sha256"
`pragma protect key_keyowner = "Xilinx"
`pragma protect key_keyname= "xilinxt_2021_07"
`pragma protect key_method = "rsa"
`pragma protect key_public_key
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAvyr1vj1oMct1BYueFRx0
/cf6aPkgzIjCFpPHosRvAsY1i7yjxwdWIdY441tDTTq+UAynD/CU79R/86JXIZct
heAebBBkOyeT5DwZijkvXtkOeY+0d1QFU+DFhlBo6Dv92e3F5XFyDHLms40HdSMK
7cL7z6TaT2YuKTxmr7qnUq87sfTTpbUu6LImP6jML3F3pAe8FDNRvLHxPha5lQAV
usx1MB/T9Iruf4868T2BqMJCWjAFaZK6V3OnKhhFKFXKtK+zpWqVN7XWqORxW7L/
97pZhLiVE5COh22lTbEBEfZGHYzZwlHaIFGCHVxkV+pGRF3ng00bHRko9asLI/qn
lQIDAQAB
`pragma protect control xilinx_configuration_visible = "false"
`pragma protect control xilinx_enable_modification = "false"
`pragma protect control xilinx_enable_probing = "false"
`pragma protect control xilinx_enable_netlist_export = "false"
`pragma protect control xilinx_enable_bitstream = "false"
`pragma protect control xilinx_schematic_visibility="false"
`pragma protect control decryption=(xilinx_activity==simulation) ? "false" : "true"
`pragma protect end_toolblock = ""
```

The first part is the commonblock, which is IEEE 1735-approved and largely controls the permissible behavior of the encrypted file during use. For the meaning of each option, refer to Xilinx's webpage, [Common Block Definition](https://docs.amd.com/r/en-US/ug1118-vivado-creating-packaging-custom-ip/Common-Rights?tocId=JDVugHeJbZpDpJ5Ya6f8~A). Compared to industry counterparts like Synopsys, Cadence, and Mentor Graphics, AMD’s documentation is exceptionally user-friendly.

The second part is the toolblock, which is for the encryption tool and includes settings such as setting encryption to rsa and specifying the public key content. Due to the standards, other encryption methods are not permissible.

Lastly, there are proprietary tool rights, such as whether netlists can be exported, bitstreams can be exported, etc., further details can be found in AMD's own documentation [AMD Tool Rights](https://docs.amd.com/r/en-US/ug1118-vivado-creating-packaging-custom-ip/AMD-Tool-Rights).

You can then encrypt using Vivado:

```tcl
# encrypt.tcl
encrypt [‑key <arg>] ‑lang <arg> [‑batch <arg>] [‑ext <arg>] [‑quiet]
    [‑verbose] [<files>...]
```
* -key refers to the keyfile.txt written above
* -batch specifies filelist.f, listing all the files you want to encrypt
* -ext refers to the extension of the output file. If not specified, Vivado will overwrite the original file. It is recommended to change .v to .vp and .sv to .svp for encryption, so Vivado can properly identify the file type when importing.

Run it in shell:
```bash
vivado -mode batch -source encrypt.tcl -nolog -nojournal
```

The last two options are purely to avoid Vivado generating log and journal files everywhere—although you can enable them for debugging.
This way, you can obtain a batch of encrypted files.

## Cadence Xcelium

Xcelium is Cadence's third-generation logic simulator, replacing the previous generation incisive’s ncsim. Xcelium commands just replace nc in ncsim with x or xm, and the encryption command changes from ncprotect to xmprotect. You can see related options by using `xmprotect -help`.

Options you might use include:
* -outdir: The folder where the command outputs, and if the folder doesn't exist, the output will be in the execution location
* -language: Choose between vhdl or vlog
* -extension: Not very useful, it allows you to change the output from source.svp to source.svp.pppp
* -ifileprotect: Encrypt parts of file content using `pragma protect begin/end`
* -level1autoprotect: Equivalent to VCS's auto2protect, retaining the interface
* -noprotdef: Don't encrypt ifdef endif define blocks
* -overwrite: Overwrite existing encrypted files

### Xcelium Automatic Encryption

With options, there are the following encryption methods:
* xmprotect dut.sv: Use the fixed 256-bit AES key CDS_DATA_KEY to encrypt the code.
* xmprotect -autoprotect dut.sv: Encrypts the AES key with CDS_RSA_KEY_VER_2 using asymmetric key, and the output format is Xcelium instead of IEEE1735 format.

Encrypted files can only be used to run simulations on Xcelium, not for synthesis or other purposes; the content of encrypted files will not appear in waveform files, and level1autoprotect files will only show the interface.

### Xcelium IEEE1735 Encrypted Cadence Key

Automatic encryption can use the option

* -v2_ip1735 Use the second edition of the IEEE1735 standard
* -v3_ip1735 Use the third edition of the IEEE1735 standard

This will use CDS_RSA_KEY_VER_2 to encrypt the AES key and output in a format compliant with IEEE1735. I recommend using the third edition when delivering to others, as HMAC is more secure than SHA2 for rights management.

### Xcelium IEEE1735 Encrypting with Own Key

Not using the CDS_RSA_KEY_VER_2 key, you can use a self-generated asymmetric key. The key used by Xcelium is in DER format, and although Xcelium provides key generation functionality, I personally suggest using openssh to generate keys, as openssh is more widely used and its generation functionality has been reviewed by more people.

If you dare to use Xcelium to generate keys, the command is:
```bash
xmprotect -over -rsakeygenerate -keylength 2048 -keyname rsakey -seed "It's MYGO!!!!!"
```
It will generate rsakey.pub and rsakey.prv.

A more formal method is to use openssh to generate a key pair:
```bash
ssh-keygen -m PEM -t rsa -b 2048 -f ./rsakey
openssl rsa -in ./rsakey -out rsakey.prv -outform DER
openssl rsa -in ./rsakey -out rsakey.pub -outform DER -pubout
```

Or directly generate a DER format private key with openssl genpkey
```bash
openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:2048 -outform DER -out rsakey
cp rsakey rsakey.prv
openssl rsa -in ./rsakey -out rsakey.pub -outform DER -pubout
```

Whether it’s ssh-keygen or openssl genpkey, unlike xmprotect, these do not use a fixed seed and produce different results each time they are executed. In a way, this is a testament to ssh-keygen/openssl being better than xmprotect.

After generating the keys, first write an encryption parameter file enc.param, version can be 2/3, and data_method allows different security strengths.
```ini
version = 2
encrypt_agent = "Crychip"
encrypt_agent_info = "Test Encryption"

key_keyowner = keydb
key_method = rsa
key_keyname = rsakey.pub

data_method = "aes128-cbc"
```

When encrypting, Xcelium will look for the specified key_keyowner/key_keyname in the environment variable XMPROTECT_KEYDB, so:

1. Place the generated rsakey.pub and rsakey.prv under the keydb folder
2. Set the environment variable \`setenv XMPROTECT_KEYDB \`pwd\` \`
3. During encryption, add -parameter to use the custom enc.param file for encryption
```bash
xmprotect -outdir encrypted -parameter enc.param -over -fcreate src/dut.sv
```
4. When delivering, send the rsakey.prv along with the encrypted files to the recipient. The recipient should also place rsakey.prv under the keydb folder to decrypt it.
