# Advanced Query Logic Analysis - Daily Sales Report_2025

Based on visual semantic query references (`queryRef`) in `visual_queries.json`.
This identifies likely complex business logic usage, not full DAX formulas.

- Total visual query objects: 36
- Total unique query references: 55
- Heuristic complex candidates: 26

## Most Complex-Likely References
- `MTD Budget Elapsed Logic.Calc Budget Daily Avg` | score=4 | used_in_visuals=4 | sections=CFO View, Stacked Exec Dashboard | matched=calc, budget, ly, mtd
- `MTD Budget Elapsed Logic.Calc Budget Daily Units` | score=4 | used_in_visuals=1 | sections=Stacked Exec Dashboard | matched=calc, budget, ly, mtd
- `SorDetail.Calc Index to Budget Bookings` | score=3 | used_in_visuals=3 | sections=CFO View, Stacked Exec Dashboard | matched=calc, index, budget
- `ArTrnDetail.Calc AR Index to Budget` | score=3 | used_in_visuals=2 | sections=Stacked Exec Dashboard | matched=calc, index, budget
- `ArTrnDetail.Calc AR Index to LY` | score=3 | used_in_visuals=2 | sections=Stacked Exec Dashboard | matched=calc, index, ly
- `GenTransaction.Calc % to LY` | score=3 | used_in_visuals=1 | sections=CFO View | matched=calc, %, ly
- `GenTransaction.Calc Index to Budget` | score=3 | used_in_visuals=1 | sections=CFO View | matched=calc, index, budget
- `SorDetail.Calc B(W) LY` | score=2 | used_in_visuals=3 | sections=CFO View, Stacked Exec Dashboard | matched=calc, ly
- `ArTrnDetail.Calc Daily Avg LY Units` | score=2 | used_in_visuals=1 | sections=Stacked Exec Dashboard | matched=calc, ly
- `ArTrnDetail.Calc Daily Avg Units` | score=2 | used_in_visuals=1 | sections=Stacked Exec Dashboard | matched=calc, ly
- `MTD Elapsed Logic Pt 2.% Elapsed` | score=2 | used_in_visuals=1 | sections=Stacked Exec Dashboard | matched=%, mtd
- `Sum(SorDetail.MTD Current Year)` | score=1 | used_in_visuals=7 | sections=CFO View, Daily Trends, Stacked Exec Dashboard | matched=mtd, current
- `Sum(GenTransaction.Calc LY)` | score=1 | used_in_visuals=4 | sections=CFO View, Stacked Exec Dashboard | matched=calc, ly
- `Sum(ArTrnDetail.Calc MTD $)` | score=1 | used_in_visuals=3 | sections=Daily Trends, Stacked Exec Dashboard | matched=calc, mtd
- `GenTransaction.Calc Avg Ship` | score=1 | used_in_visuals=2 | sections=CFO View, Stacked Exec Dashboard | matched=calc
- `MTD Elapsed Logic Pt 2.Today's Date` | score=1 | used_in_visuals=2 | sections=CFO View, Stacked Exec Dashboard | matched=mtd
- `SorDetail.Calc Avg Books` | score=1 | used_in_visuals=2 | sections=CFO View, Stacked Exec Dashboard | matched=calc
- `Sum(ArTrnDetail.MTD Current Units)` | score=1 | used_in_visuals=2 | sections=CFO View, Stacked Exec Dashboard | matched=mtd, current
- `Sum(ArTrnDetail.MTD Last Year Units)` | score=1 | used_in_visuals=2 | sections=CFO View, Stacked Exec Dashboard | matched=mtd, last year
- `Sum(GenTransaction.MTD Current Year)` | score=1 | used_in_visuals=2 | sections=CFO View | matched=mtd, current
- `Sum(SorDetail.MTD Current Units)` | score=1 | used_in_visuals=2 | sections=CFO View, Stacked Exec Dashboard | matched=mtd, current
- `Sum(SorDetail.MTD Last Year Units)` | score=1 | used_in_visuals=2 | sections=CFO View, Stacked Exec Dashboard | matched=mtd, last year
- `Sum(SorDetail.MTD Last Year)` | score=1 | used_in_visuals=2 | sections=CFO View, Stacked Exec Dashboard | matched=mtd, last year
- `SorDetail.Calc Avg Units` | score=1 | used_in_visuals=1 | sections=Stacked Exec Dashboard | matched=calc
- `SorDetail.Calc B(W) Units` | score=1 | used_in_visuals=1 | sections=Stacked Exec Dashboard | matched=calc
- `SorDetail.Calc Product Unit Type` | score=1 | used_in_visuals=1 | sections=Backlog Detail | matched=calc

## Sections with Highest Logic Density
- `Stacked Exec Dashboard` | complexity_score=51 | unique_refs=32
- `CFO View` | complexity_score=37 | unique_refs=26
- `Daily Trends` | complexity_score=4 | unique_refs=8
- `Backlog Detail` | complexity_score=2 | unique_refs=16

## High-Value Targets to Extract Full DAX First
- `MTD Budget Elapsed Logic.Calc Budget Daily Avg`
- `MTD Budget Elapsed Logic.Calc Budget Daily Units`
- `SorDetail.Calc Index to Budget Bookings`
- `ArTrnDetail.Calc AR Index to Budget`
- `ArTrnDetail.Calc AR Index to LY`
- `GenTransaction.Calc % to LY`
- `GenTransaction.Calc Index to Budget`
- `SorDetail.Calc B(W) LY`
- `ArTrnDetail.Calc Daily Avg LY Units`
- `ArTrnDetail.Calc Daily Avg Units`
- `MTD Elapsed Logic Pt 2.% Elapsed`
- `Sum(SorDetail.MTD Current Year)`
- `Sum(GenTransaction.Calc LY)`
- `Sum(ArTrnDetail.Calc MTD $)`
- `GenTransaction.Calc Avg Ship`
- `MTD Elapsed Logic Pt 2.Today's Date`
- `SorDetail.Calc Avg Books`
- `Sum(ArTrnDetail.MTD Current Units)`
- `Sum(ArTrnDetail.MTD Last Year Units)`
- `Sum(GenTransaction.MTD Current Year)`
- `Sum(SorDetail.MTD Current Units)`
- `Sum(SorDetail.MTD Last Year Units)`
- `Sum(SorDetail.MTD Last Year)`
- `SorDetail.Calc Avg Units`
- `SorDetail.Calc B(W) Units`