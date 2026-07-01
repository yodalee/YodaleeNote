---
title: Digital Circuit Design Series - INNOVUS Floorplan
date: 2026-06-11
categories:
- ICdesign
tags:
- ICdesign
series:
- ICdesign
AITranslated: true
---
After preparing the offline materials, this article starts operating INNOVUS for layout.
In fact, I was really uncertain about what to write because I don't have INNOVUS available at hand, and without screenshot images (unless I steal them), talking only about procedures feels like a manual. Therefore, this article was left unwritten for a while.

In the end, I still wrote it, adding some personal experiences and terminology explanations along with the steps. Because the article ended up being quite long, I've split it into three parts: Floorplan, Powerplan, and P&R.

However, please note these three points:
1. It is recommended to thoroughly read the earliest written [Chip Physical Structure]({{< relref "chipstructure" >}}), explanations won't be repeated here.
2. The previous article [APR Preparation]({{< relref "APRmaterial" >}}) also won't be reiterated; make sure you've prepared everything from that article.
3. There are many odd steps in layout; this article can only cover a small portion. In practice, you won't be able to design a chip just by following this article, many fine details require hands-on experience, or one-on-one instruction to grasp.
4. My personal experience is only up to 40nm, as far as I know, this experience broadly applies up to 28nm, at most 22nm. Beyond that, reaching 16nm and FinFET, the APR process is a completely different story.

I’ve heard tales that can be summed up as **Big Billion Errors**, simply put, they did a 16nm or 7nm FinFET APR and the layout DRC resulted in a billion errors, leaving only a month before tapeout. Fortunately, they managed to fix those billion errors within a month and successfully completed the process.

I likely won't have the opportunity to work on FinFET in my lifetime; seek out those with relevant experience if problems arise.

# Basic Process

First, let's have a basic understanding of APR. The following is a general APR process I've compiled:

* Import Design/IO: Import the synthesized Verilog code from the design compiler, set IO positions
* Floorplan: Place the necessary Macros, set blockages
* PowerPlan: Place Power Ring, Power Stripe, Follow Pin
* PowerCheck: Conduct power analysis using INNOVUS integrated Voltus
* Placement: Place each standard cell on Follow Pin
* Clock Tree Synthesis (CTS): Synthesize clock tree
* Route: Actually connect the circuit
* Signoff: Final timing check

# Remember to Save

APR is a time-consuming process, sometimes pressing a key can take several hours, and most actions are irreversible. Thus, running INNOVUS is just like playing an RPG, the **most important thing is to save**, better than having to redo everything later.
Below is a personal habit that you may want to follow; I use numbers at the beginning to distinguish stages, each stage’s save follows the order:

* init: Import files and save for the first time after setting up full-domain power.
* 0 Power plan, from the beginning until all power-related settings are completed, includes the following stages:
  * 0Macro: After placing Macro
  * 0PowerRing: After placing Power Ring and Macro Ring
  * 0PowerStripe: After setting Power Stripe
  * 0PowerFollowpin: Running the first stage of Power Analysis with Follow pin
  * 0Power_drcfix1: Fix errors detected by INNOVUS built-in DRC
  * 0Power_drcfix2: Fix errors detected by Calibre DRC after exporting Floorplan
* Starts with 1, from Place until CTS is completed
  * 1placed: After executing placement
  * 1prects: After fixing pre-cts Timing Violations post-placement
  * 1cts: After executing CTS
  * 1postcts: After setup time/hold time adjustments post-CTS
* Starting from Route to complete remaining signoff process
  * 2routed: After executing Route
  * 2routed_setup: Fix Setup timing violations
  * 2routed_hold: Fix Hold timing violations
  * 2signoff: After completing the final signoff with Tempus and saving
* Filler: Insert Filler cell, metal fill, and finally save. You shouldn't need to do anything when opening this file; export it to get the gds file needed for the process.

This save order isn’t fixed. For example, 0Power_drcfix1 existed because adding Power Stripe easily led to DRC violations, learning to use blockage layer has greatly alleviated this issue.
If it's advanced processes, perhaps more stages of saves are needed.

# INIT

## Import Files

Select `File` -> `Import Design`
* Choose the synthesized *.syn.v from Netlist, input the top cell name (I don't quite let it capture on its own, afraid of errors)
* Select the converted macroLib from Reference Libraries
* Select the chip_top.io written in the previous article from FloorPlan
* Input VDD VSS for Power
* Choose the .mmmc file written in the previous article~~or left by a predecessor~~ for MMMC

## Set Power

When importing design, two virtual global powers, VDD and VSS, were set. We now need to connect the actual standard cells using power to these two global powers.

Click `Floorplan` -> `Connect Global Nets`:
* Enter Pin Name(s) as VDD, To Global Net as VDD, and press `Add to List`
* Enter Pin Name(s) as VSS, To Global Net as VSS, and press `Add to List`
* Choose Tie High, To Global Net as VDD, and press `Add to List`
* Choose Tie Low, To Global Net as VSS, and press `Add to List`

The same names can be confusing, the former refers to the actual pin name of the standard component, and the latter to the virtual global power name set during the import design above. Below are a few examples for better understanding of what this section does:
1. If the grounding for the standard cell is GND, change Pin Name in the second step above to GND
2. Some SRAMs in high-level processes name two groups as VDDCE (Core) VDDPE (Peripheral), while the standard cell is still VDD. In this case, the first step needs to be performed three times with Pin Name set to VDD, VDDCE, and VDDPE.

For designs with multiple powers, a common power format (.cpf) file will need to be imported. I haven't encountered this situation yet, but when I do, I'll write about it.

## Save Check

Select `File` -> `check Design`, uncheck the unfinished `Floorplan` and `Placement`, check Display HTML; after inspection, a simple webpage will pop up showing the results.

The most critical thing to look for is the following (or something equally severe that I haven’t encountered yet):
> Cells with missing timing data
{.error}

This indicates that some cells lack timing data, usually due to failure in importing the black box .lib file in the MMMC file. Missing this data means you can't proceed to CTS, so make sure to correct it before moving forward.

After checking and finding no issues, save the layout as init. In my experience, you'll use it at least 3-4 times.
You can also copy the above steps and save them in script/init.tcl for reuse when design changes occur.

# FloorPlan

Once the design is imported, the first step is to determine the Floorplan.

## What is Utilization
Utilization refers to the ratio of the total area of the existing chip’s standard cells to the actual chip area. The highest at 1.0 means only standard cells, with no other space.

0.7 is a general start, it can be lower if the memory (black box) occupies a high proportion. As mentioned in the article [1P3M]({{< relref "1P3M" >}}), a design with no black box, I managed to push it up to 77%.

When getting a new process and wanting to familiarize with the entire layout process, I suggest starting with a very low utilization rate of about 0.4~~wasting sand~~, and layout once to ensure all settings such as clock buffer/inverter, signoff DRC LVS etc., are fine before compressing area to challenge limits.
If the U rate is set too high, **usually** there won’t be obvious symptoms, it won’t crash like BSOD. APR software perseveres and never gives up easily, trying until it can't anymore. Generally, lowering the U rate gradually leads to issues at various stages:
* Once, I went crazy and set U rate to 0.9, and during placement, I encountered a lot of errors, couldn't fit in.
* U rate 0.85, at the final step of Routing, a Timing violation occurred, ECO couldn't fix it, one very long path couldn't be resolved.
* At U rate 0.8, after CTS, Design Rule Violations (DRVs) of Capacitance and Transition violations occurred, and ECO couldn't fix them.
* U rate 0.7, thankfully, **gladly** went smoothly to the end.

Once Timing violation occurs, it's probably game over, you can only raise the target slack value a bit higher to see if INNOVUS is willing to solve it; input/output may depend on whether synthetic input_delay/output_delay can make up this difference.
If DRVs occur, you can take a chance to see if the final chip works; I took a chance once and won.

## Set FloorPlan

Select `Floorplan` -> `Specify Floorplan`.
Generally, unless specified otherwise, I just use W/H Ratio = 1 and Urate to set, allowing INNOVUS to decide the final width and height.
Seeing that width and height are not integers, don’t let OCD flare up, its height must be an integer multiple of the M1 followpin height, not arbitrary values.

For Core Margin settings, refer to the Power Ring section in the next article.

## Placing Black Box

If you want INNOVUS to place the black box, use `Floorplan` -> `Generate Floorplan` -> `Place Macro`. It will calculate the best position for the black box according to the overall design, but I have encountered two issues:

1. This step moves my IO pad, change the place_status in [IO Settings](https://yodalee.me/2025/05/aprmaterial/#io-%E8%A8%AD%E5%AE%9A) to fixed.
2. This step places the black box in the middle of the chip based on the overall situation, while we usually place the black box towards the edges to leave as complete a space as possible in the middle for standard cell use.

I don’t use the automatic `Place Macro`, instead, I use `Floorplan` -> `Floorplan toolbox`.
The introduction to this toolbox can be found at [Graphical Interface Introduction<Floorplan ToolBox>](https://www.sohu.com/a/383153201_99933533).
I use alignment with Core boundaries, place a black box to the edge, and then align the other black boxes sequentially (I must say, placing them on the edge might be human bias, placing towards the center could potentially be more efficient).

Make sure to set the distance between two black boxes properly, if memory with Power Ring, remember to include it, generally 1μm is quite ample (yes, in the realm of chips where linewidth is only 0.1 μm, 1μm is a huge distance).

After placing the black box, change their status to fixed.
```tcl
set_instance_placement_status -all_hard_macros -status fixed
```

## Blocking Layer

There are two types of blockages in INNOVUS layout:
* Place blockage: Don’t place standard cells here.
* Routing blockage: Unless necessary for passing through here (e.g., connecting to a black box), avoid routing here.

Black box settings related to blockage are called Halo ~~the Halo series~~, including Placement Halo and Routing Halo. There aren’t fixed rules for setting Halos, here are some principles for your reference:
1. Generally, Placement Halo is 1μm; Routing Halo is 0.5μm.
2. If two black boxes are placed very close, placement halo must fill the gap between them.
3. If the black box has a power ring, the placement blockage must encompass the entire ring; otherwise, INNOVUS will place cells under the power ring, easily causing routing errors and timing violations.

Use `Floorplan` -> `Edit Floorplan` -> `Edit Halo` to edit:
* Choose `Placement Halo` -> `All Blocks`
* Set the top, bottom, left, and right all to 1 and `Apply`
* Choose `Routing Halo`
* Set the top, bottom, left, and right all to 0.5 and `Apply`

For more granular control, you can also choose `Selected Block/Pad` to set Halo values for individual black boxes.

INNOVUS has a *magical design*: follow pins will grow wherever standard cells can be placed. 
So if there are gaps within the placement halo, you will see some short follow pins growing, or even some standard cells being placed, which easily breeds DRC errors and routing timing violations.

# Conclusion

In this chapter, we completed the overall Floorplan of the chip, like planning the layout of a house, deciding how thick the walls are and how to partition the rooms. Don’t take it too seriously, use common values for Floorplan like a U rate of 0.7 and there's a high chance it will be successful. If concerned about chip operation, just allocate a bit more space initially, giving a Macro distance of 2μm won't hurt.
The next chapter moves on to Power Plan, starting wiring the electricity for the house.