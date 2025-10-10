---
title: Digital Circuit Design Series - Introduction
date: 2023-11-16
categories:
- ICdesign
tags:
- ICdesign
series:
- ICdesign
AITranslated: true
lang: en
---
The story goes like this: Recently, after many years, I delved back into digital circuit design and tapeout, a field I had been distant from for quite a while. On November 13th, with the pressure on, I submitted my first ever digital circuit chip. I'm writing this preface to document future related posts.

The last time I dabbled in digital circuit design was during my university days, even before I started this blog, which shows how long ago it was. I wanted to write this article because I found very few related records and articles online during this tapeout process. The articles I did find were either in Simplified Chinese or English. The only detailed Traditional Chinese one I found was [HaoYu's Notes](https://timsnote.wordpress.com/digital-ic-design/). Besides that, I had to rely on my college classmates for help. Sending out this tapeout on 11/13 was largely thanks to their tremendous support, including long-term partner *JJL* and *phoning*, whose support I've relied heavily upon from university through graduate school to now.

It's quite strange really, given that we claim to be the **Silicon Island**, **Chip Island**, the world's leading semiconductor kingdom, yet there's more and newer teaching material in American universities than in Traditional Chinese. Looking at IC design, several recent startups with new digital ICs like mining machines and AI chips are made in China and the U.S. So where have all of Taiwan's digital circuit design talents gone?

With a spirit of paving the way for future generations, I've decided to document my entire tapeout process, even though I am still a novice. I hope to leave behind more articles for future reference and if they can clear up confusions or prevent others from hitting walls, then these articles have their value.

Of course, integrated circuits are profoundly complex and are definitely among the most complicated human inventions. People who can master all aspects are extremely rare. If my articles contain any errors, please feel free to correct me. I’m not concerned with maintaining appearances—I’ll readily admit when I don’t know something~~third base~~, rather than pretending to know and misleading others.

----

Currently, these are the topics and outlines I have in mind to write about. I haven't planned how many articles I will write yet, but there will be a dedicated [category]({{< relref "/categories/ICdesign" >}}) to collect these types of articles:

* [Overview of the Tapeout Process]({{< relref "chipflow" >}})  
  Introduction to the tapeout process, including verilog/simulation, synthesis, post-synthesis simulation/LEC, APR, post-layout simulation, DRC/LVS verification.
* [Design Constraint]({{< relref "designconstraint" >}})  
  Introduction to various characteristics of digital circuits, such as frequency, load, input/output timing. This article is applicable to both FPGA and tapeout designs and also lays the foundation for Design Compiler and synthesis.
* [Design Compiler]({{< relref "designcompiler" >}})  
  Introduction to Synopsys's foundational tool, [Design Compiler](https://www.synopsys.com/implementation-and-signoff/rtl-synthesis-test/dc-ultra.html), covering how to set up the software correctly and what actions Design Compiler takes during synthesis.
* [APR: Physical Structure of a Chip]({{< relref "chipstructure" >}})  
  Introduction to the internal architecture of a chip, such as pads, bonding wires, memory, power rings, power strips, etc., for a clear understanding of what APR does.
* APR: Innovus Setup Process:  
  An overview of the steps needed for APR using Cadence's [Innovus](https://www.cadence.com/zh_TW/home/tools/digital-design-and-signoff/soc-implementation-and-floorplanning/innovus-implementation-system.html), instead of Synopsys's [ICC2](https://www.synopsys.com/implementation-and-signoff/physical-implementation/ic-compiler.html), will be included as well. The article will walk through most of the files needed for layout, and highlight the stumbling blocks I encountered during this layout (there were quite a few, much to my frustration).
* Verification:  
  DRC and LVS. After so many years, and even after having developed a DRC engine myself, I now face deciphering the DRC violations tools output for me. These are real violations, not "missing" or "false" violations. On top of that, I have to deal with the LVS report's grinning face from GY.