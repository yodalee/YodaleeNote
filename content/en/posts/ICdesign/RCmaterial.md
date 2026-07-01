---
title: RC Extraction Settings
date: 2025-09-29
categories:
- ICdesign
tags:
- ICdesign
images:
- /images/ICdesign/RCmaterial.png
AITranslated: true
---
When you are in the Warring States period, traveling around the various states is a necessary skill.

In the previous articles on [design constraint]({{< relref "designconstraint">}}) and [design compiler]({{< relref "designcompiler" >}}), it was mentioned that each path in a chip is checked to ensure that the delay between each set of registers meets the Timing Constraint. This check is crucial because if the Timing Constraint is not met, the chip can only operate at a downgraded specification.

When using a design compiler, this value only includes the delay of the logic gate itself and does not include the physical effects of the actual layout wiring and connection wire length. This is why, during synthesis, if you specify fixing hold time issues (by adding set_fix_hold to the script), the design compiler might insert a large number of buffers. To the design compiler, the delay of connections does not exist, so hold time needs to be corrected for all registers without logic gates.

Including this option has disadvantages, such as prolonging synthesis time and causing the design compiler to overestimate power consumption; these buffers might also be removed during the actual APR because their connection delay is already considered, making the work futile. Even though major companies like Synopsys' Fusion Compiler attempt to integrate synthesis with APR to incorporate actual layout position information during synthesis, what can be obtained during the synthesis stage is still only estimated timing.

# What is RC extraction?

As design enters Place & Route, signal delay can take into account physical factors such as actual metal routing and coupling capacitance between adjacent lines. At this time, it is necessary to perform RC extraction to extract the resistance and capacitance values on each connection, calculate the delay on each path in the layout based on the parasitic parameters, and then send the delay into timing analysis tools such as Synopsys' PrimeTime or Cadence's Tempus, completing the final Signoff process and Static Timing Analysis (STA), ensuring that the chip can still meet the timing goals after all parasitic effects are considered.

Through STA tools, final results in the form of a spef file (Standard Parasitic Extraction Format) are obtained. The spef format is an IEEE standard; you can refer to the same person's blog [understanding SPEF](https://ileonsun.github.io/understanding-spef/). The spef can be imported into the layout for simulation to ensure that the chip can still operate normally under real delay. Without this step, we would not be able to simulate layout delay before manufacturing and would not be able to complete Timing Constraint analysis.

Due to the importance of RC extraction, all companies provide RC extraction solutions, including:
- Synopsys [StarRC](https://www.synopsys.com/implementation-and-signoff/signoff/starrc.html)
- Cadence [Quantus QRC](https://www.cadence.com/en_US/home/tools/digital-design-and-signoff/silicon-signoff/quantus-extraction-solution.html)
- Mentor [Calibre xACT](https://eda.sw.siemens.com/en-US/ic/calibre-design/circuit-verification/xact/), also known as xCalibrate

I am not very familiar with this part and am unsure which company takes the largest share. Anyway, the story begins here.

Parameters that affect RC values include the resistivity and thickness of the wiring material (usually copper); what dielectric is used between the wiring? How many layers of metal does the process use? The people who truly know are the wafer foundries; therefore, to make a chip, you first need to obtain the process PDK from the foundry, which will contain the necessary parameter files for process RC extraction. Among the three giants, who are the Wei, Wu, and Han kingdoms? XD, none of the three can dominate the world. Not all foundries are "pocket Michael Michael," so naturally, not every tool's data is supported.

In the case described in the [1P3M]({{< relref "1P3M" >}}) article, I obtained Synopsys' itf file, but I am familiar with Cadence's INNOVUS, which integrates QRC. INNOVUS requires .tech and .CapTbl files for mmmc settings, hence this article introducing various files needed for RC extraction and how to convert between different tools when not available.

Of course, I haven't used all the tools; I can only record the processes I've gone through or refer to online notes for organization. If there are processes not recorded, feel free to supplement.

# Original Format

Calling it the original format is a bit strange because the content isn't original. Here, it means: how does the foundry provide process information to EDA tools?

These files record information such as:
- Dielectric coefficients, thickness, and number of layers of inter-wire fillers
- Models for capacitance change with temperature
- How the process affects capacitance values
- Unit resistors for different widths and thicknesses
- Parameters for resistivity change with density and width, etc.

The formats used by each company are as follows:
- Synopsys .itf format (Interconnect Technology Format)
- Cadence .ict format (InterConnect Technology file)
- Mentor .mipt format (Mentor Interconnect Process Technology)

Currently, only the file format of itf is parsed online [understanding ITF](https://ileonsun.github.io/understanding-itf/), and ict and mipt file formats are not public yet. However, if you have ict or mipt files, you can open them with a text editor, and they should be quite understandable.

# Original Format Conversion

Since the foundry may only provide one company's file (e.g., the process I obtained only had an .itf file), to capture market share, all three EDA companies offer some tools to convert one company's original format into another. After searching, I've only found ways to convert itf into ict and mipt, not the reverse. However, according to my AI tool summary:

> The earliest to appear / commercialized the earliest: Avanti's Star-RC (later became Synopsys StarRC).
> Avanti had Star-RC products in the 1990s (public reports on Star-RCXT can be seen in 1999), and Avanti was later acquired by Synopsys (the transaction was completed between 2001–2002), making StarRC a part of Synopsys' product line.
> [EDN+1](https://www.edn.com/avantis-new-star-rcxt-engine-speeds-time-to-market-and-ensures-timing-convergence-for-vdsm-designs/)

It is indeed possible that StarRC gained a competitive advantage by establishing a de facto standard early in this area, leading foundries to generally support the itf format specified by StarRC, although I have no evidence for this.

## Synopsys itf to Cadence ict

Using the executable `itf_to_ict` under voltus/gift in innovus, located at `INNOVUS/share/voltus/gift/bin/itf_to_ict`:
```bash
itf_to_ict *.itf *.ict
```

## Synopsys itf to Mentor Mipt

Refer to the discussion on [how to convert mipt to itf](https://bbs.eetop.cn/thread-967787-1-1.html)
```
xcalibrate -itf2mipt2 itf_file 
```
Generates out.mipt.

# Lookup Files and RC Extraction

Above introduces the original format. Generally, tools do not directly use such files when calculating RC, as it would be too laborious to parse every connection repeatedly, such as calculating how many layers of dielectric exists between M1-M2.

In actual RC extraction, tools first convert data into tables, pre-calculating RC values based on execution conditions. RC extraction tools calculate parasitic capacitance and resistance in designs using a lookup method, saving a lot of computation time.

Below are the lookup formats for each company and how to convert from the original format to the lookup format. This conversion takes more time, and the more complex the advanced process files, the longer it takes. Therefore, two recommendations:
1. Most tools have multi-core options to some extent. As life is short, open as many as you can. If possible, upgrade to multi-core computers or **switch to a company that allows computer upgrades**.
2. Immediately check if the required files are provided when receiving the work, and hurry up with conversion if not; otherwise, this would become a bottleneck hindering subsequent layout work.

As a reference, the machine used in the tests below had 32 GB of memory and a Xeon Platinum 8268 CPU @ 2.9 GHz with 16 cores, and the conversion involved a 3-layer metal process.

## Synopsys

### 1 .nxtgrd

The lookup file used by StarRC for parasitic parameter extraction, generated from itf using StarRC grdgenxo
```bash
grdgenxo *.itf
```

This step takes a lot of time. Refer to [using multiple cores with grdgenxo](https://blog.csdn.net/m0_61544122/article/details/146949384) to add a config file.
```bash
$ cat config
NUM_CORES: 16
GRD_DP_STRING: list ssh localhost:16
$ grdgenxo -dp_config config *.itf
```
**Time required: 7 minutes 50 seconds**.

### 2 .tluplus

The lookup file for resistance and capacitance used by Synopsys APR tool ICC2, also generated using the StarRC tool grdgenxo.

```bash
grdgenxo -itf2TLUPlus -i *.itf -o *.tluplus
```

You cannot use dp_config when using this option, but when you previously converted .nxtgrd files, you could simultaneously convert the prerequisite files for .tluplus, meaning the command below just exports the files, finishing in milliseconds. Even if you haven't run .nxtgrd before, itf to .tluplus conversion is relatively quick, **taking about 30 seconds**.

### 3 Reverse .itf File

grdgenxo can reverse convert nxtgrd files back to .itf **reversing technique** because the original itf is commented in the nxtgrd header during itf to nxtgrd conversion:
```bash
grdgenxo -nxtgrd2itf -i *.nxtgrd -o *.itf
```

## Cadence

Cadence's lookup files have two types

### 1 .tch

Quantus technology files, generally with the .tch extension, generated from ict to .tch and .CapTbl using Cadence Quantus Extraction (EXT191) under Techgen:

```bash
Techgen -cell -multi_cpu 16 -plan *.ict
Techgen -cell -parallel -autoconcat *.ict *.tch
```

This takes tremendously long and doesn't support multi-core. A 3-layer metal process takes **6-7 hours** to convert, making one wonder how long advanced processes would take. This setting references [how to generate .tch file](https://www.edaboard.com/threads/how-to-genrate-tch-file.249128/)

### 2 .CapTbl

Uses generateCapTbl from innovus, which also requires some time to compute extrapolated capacitance tables, about **1 hour** without multi-core support.

Additionally, this conversion requires the basic process parameters in a .lef file:
```bash
generateCapTbl -lef *.lef -ict *.ict  -output *.CapTbl
```

## Mentor

### rules.R rules.C

The parameter files used by Mentor are rules.R and rules.C, corresponding to resistance and capacitance extraction, respectively, generated using xcalibrate

```bash
xcalibrate -exec -turbo 16 *.mipt
```

Actual conversion **4 minutes**.

# Summary

If multi-core is used, preparing files is generally a matter of minutes, except Cadence's Techgen and generateCapTbl, which cannot use multi-core, requiring several hours for conversion. Honestly, it's 2025, and not supporting multi-core is a bit embarrassing. **Cadence, please do better**.

Let me summarize with a table and a picture.

| Company | Original Format | Lookup Format |
|-|-|-|
| Synopsys (StarRC)       | .itf           | .nxtgrd <br /> .tluplus   |
| Cadence (QRC/Quantus)   | .ict           | .capTbl, .tch      |
| Mentor (Calibre xRC/xACT)| .mipt         | rules.C rules.R    |

Conversion illustration:

![RC format and the translate tools](/images/ICdesign/RCmaterial.png)