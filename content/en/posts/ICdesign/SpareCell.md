---
title: ECO cell and Spare Cell
date: 2025-09-10
categories:
- ICdesign
tags:
- ICdesign
AITranslated: true
---
This article is similar to the previous DFT, introducing ECO, something I haven't fully tried yet, and how we support ECO in design, along with the most commonly used ECO solution in layout, Spare Cell.

When your chip reaches product level, you may need to consider ECO issues. ECO stands for Engineering Change Order, and you can refer to the following article for more information: [What is ECO in Chip Design?](https://cloud.tencent.com/developer/article/1892478).
If I had to summarize it in one word, ECO is the process of discovering design problems, where formal procedures have been completed and there is no time to use the formal approach within the schedule, so engineering methods are used to forcibly resolve the issue, like the example of [the building in New York that was found to be potentially unstable and reinforced with steel plates](https://www.youtube.com/watch?v=Q56PMJbCFXQ) to ensure safety.

The three-stage ECO mentioned in the above article still follows the design principle: 
> The earlier a problem is discovered, the lower the cost to fix it

The ECO/spare cell introduced in this article represents the highest correction cost. During production, the logical gates of the chip can be completed by the wafer foundry, a small part of the subsequent process is done for testing, and the rest of the metal layers are completed after ensuring that ECO is not needed. If a problem is discovered during testing, the photomask can be modified to change the metal layer routing to modify the implemented logic.

# ECO cell

First is the ECO cell, which can be imagined as a special kind of standard cell provided by the wafer foundry, which can be slightly modified into various logical cells. Not all wafer foundries offer ECO cells, and to be honest, *I've never seen what an ECO cell looks like*. Even with the following reference materials I could find, the content is mostly incomplete:
* [Metal ECO implementation using Mask Programmable cells](https://www.design-reuse.com/article/60791-metal-eco-implementation-using-mask-programmable-cells/)
* [Metal Configurable Gate Array in Metal-Only ECO](https://www.nandigits.com/gof_display_doc.php?document_type=gate_array)

By roughly referencing these, it should be understandable how it is achieved.

# Spare Cell

Since not everyone provides ECO cells, there is another way to implement ECO, which is to use the remaining space on the layout to add more spare logic gates. When ECO is needed, the wiring can be redirected to the spare logic. The inputs of these cells should be tied to 0 Ground or 1 VDD, and the outputs should be left floating to minimize power consumption.

As for which logic gates to add, it depends on the internal regulations of each company. In theory, you should be able to find the configuration left by seniors in your company.
~~If not, start your own culture~~ My own suggestions are as follows:
* One general logic gate, with a few connections like NAND, Mux, Inverter, etc., providing two to five of each
* Two D flip-flops, used somewhat like FPGA Slice
* Two BUFs
* Put one of each different size Delay Cell
* One TieHi and one TieLo to serve the entire Spare Module

Below is an example in INNOVUS tcl, requesting to place only NAND for simple logic gates, please **remember to change the cells and not copy directly**, the basic syntax is:
* -cells: specify which cells and how many of them to place
* -tie_low: cell:pin specifies which pins are grounded
* -tieoffs: specify which cell is used for tie high/low

## SPARE area

The insertion steps are generally completed before or after placement. If you insert spare cells after routing is complete, it will lead to serious timing issues. During the insertion of Spare cells, the aim is to distribute them evenly so that nearby replaceable logic gates can be found when ECO is required. This article suggests that the number be 3%-4% of the total design area, which is not insignificant.

As for how to calculate SPARE size, it will first use get_db to obtain **already placed** spare instances, and limit to one of them:

Using the tcl script from this article [Command to get cell Area](https://community.cadence.com/cadence_technology_forums/f/digital-implementation/20572/command-to-get-cell-area), sum up the cell area within the module to get the area of a module.

**ref_lib_cell_name** the property is extracted from get_cells $inst above with report_property obtained:

## Inserting Spare Cell

How to best insert SPARE_module in innovus?

First attempt:
1. Insert spare cell first
2. Execute

The result was not very even, and many SPARE cells were placed in the corners. After trying, it was more evenly distributed by doing the following:

Since the logic of opt is to respect the original placement as much as possible, moving as little as possible, a better result can be obtained.

# Comparison of ECO cell and Spare cell

What are the pros and cons of the above two ECO solutions?

The first aspect is the modification cost of both, which is the photomask. The advantage of Spare Cell is that during ECO, only the photomask of the Metal layer needs to be changed, while the photomask for the original cell fabrication remains untouched. In the case of ECO cell, since its modification is to change the wiring within a cell, Contact and the metal layer above will be involved, adding an extra layer of photomask means additional cost.

In terms of design, ECO Cell is simpler and only requires filling in a single type of ECO cell; Whereas Spare Cell can only insert fixed types of cells. NAND is just NAND, but what if this time ECO needs a lot of XORs? ECO cell can all be modified to XOR cells, offering more flexibility, whereas Spare cell may fall short.

Moreover, the ECO cells in the above references can connect more ECO cells during ECO to increase output driving force, whereas spare cell only inserts the smallest logical gates, thus having relatively smaller driving force and may lead to DRVs issues after ECO.

It can only be said that both have their pros and cons, please judge for yourself.

# How to perform ECO in INNOVUS

Once I encounter this, I'll complete this chapter.