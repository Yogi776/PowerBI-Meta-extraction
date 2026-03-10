let
    Source = Table.NestedJoin(InvMaster, {"StockCode"}, #"InvMaster+", {"StockCode"}, "InvMaster+", JoinKind.RightOuter),
    #"Expanded InvMaster+" = Table.ExpandTableColumn(Source, "InvMaster+", {"ProductUnitType"}, {"InvMaster+.ProductUnitType"}),
    #"Removed Duplicates" = Table.Distinct(#"Expanded InvMaster+", {"StockCode"}),
    #"Removed Blank Rows" = Table.SelectRows(#"Removed Duplicates", each not List.IsEmpty(List.RemoveMatchingItems(Record.FieldValues(_), {"", null}))),
    #"Removed Errors" = Table.RemoveRowsWithErrors(#"Removed Blank Rows", {"StockCode"}),
    #"Filtered Rows" = Table.SelectRows(#"Removed Errors", each ([#"InvMaster+.ProductUnitType"] <> "Retired")),
    #"Replaced Value" = Table.ReplaceValue(#"Filtered Rows","","Other",Replacer.ReplaceValue,{"InvMaster+.ProductUnitType"}),
    #"Replaced Value1" = Table.ReplaceValue(#"Replaced Value",null,"Other",Replacer.ReplaceValue,{"InvMaster+.ProductUnitType"})
in
    #"Replaced Value1"