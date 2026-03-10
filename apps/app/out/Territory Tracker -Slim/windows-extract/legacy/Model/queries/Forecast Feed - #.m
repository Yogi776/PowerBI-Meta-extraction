let
    Source = Sql.Database("nausawsdb004.harmar.lan", "Harmar"),
    dbo_GenTransaction = Source{[Schema="dbo",Item="GenTransaction"]}[Data],
    #"Filtered Rows" = Table.SelectRows(dbo_GenTransaction, each Text.StartsWith([GlCode], "4")),
    #"Filtered Rows1" = Table.SelectRows(#"Filtered Rows", each [GlYear] > 2019),
    #"Inserted Last Characters" = Table.AddColumn(#"Filtered Rows1", "Last Characters", each Text.End([SubModCustomer], 7), type text),
    #"Renamed Columns" = Table.RenameColumns(#"Inserted Last Characters",{{"Last Characters", "Salesforce Connector"}}),
    #"Filtered Rows2" = Table.SelectRows(#"Renamed Columns", each ([GlPeriod] <> 14)),
    #"Multiplied Column" = Table.TransformColumns(#"Filtered Rows2", {{"EntryValue", each _ * -1, type number}}),
    #"Added Custom" = Table.AddColumn(#"Multiplied Column", "Year-Month", each Text.From([GlYear]) & "-" & Text.PadStart(Text.From([GlPeriod]), 2, "0")),
    #"Removed Other Columns" = Table.SelectColumns(#"Added Custom",{"GlCode", "EntryValue", "SubModArInvoice", "SubModCustomer", "SubModStock", "Year-Month"}),
    #"Reordered Columns" = Table.ReorderColumns(#"Removed Other Columns",{"Year-Month", "GlCode", "SubModArInvoice", "SubModCustomer", "SubModStock", "EntryValue"}),
    #"Merged Columns" = Table.CombineColumns(#"Reordered Columns",{"Year-Month", "GlCode", "SubModArInvoice", "SubModCustomer", "SubModStock"},Combiner.CombineTextByDelimiter("|", QuoteStyle.None),"Merged"),
    #"Grouped Rows" = Table.Group(#"Merged Columns", {"Merged"}, {{"Value", each List.Sum([EntryValue]), type number}}),
    #"Appended Query" = Table.Combine({#"Grouped Rows", #"SysPro: ArTrnDetail (Merged for Join)"}),
    #"Grouped Rows1" = Table.Group(#"Appended Query", {"Merged"}, {{"Value", each List.Sum([Value]), type nullable number}, {"Units", each List.Sum([Units]), type nullable number}}),
    #"Reordered Columns1" = Table.ReorderColumns(#"Grouped Rows1",{"Merged", "Units", "Value"}),
    #"Changed Type" = Table.TransformColumnTypes(#"Reordered Columns1",{{"Units", Int64.Type}}),
    #"Split Column by Delimiter" = Table.SplitColumn(#"Changed Type", "Merged", Splitter.SplitTextByDelimiter("|", QuoteStyle.Csv), {"Year-Month", "Revenue GL Code","Invoice Number", "Customer Code", "Stock Code"}),
    #"Replaced Value" = Table.ReplaceValue(#"Split Column by Delimiter",null,0,Replacer.ReplaceValue,{"Units"}),
    #"Replaced Value1" = Table.ReplaceValue(#"Replaced Value",null,0,Replacer.ReplaceValue,{"Value"}),
    #"Merged Queries" = Table.NestedJoin(#"Replaced Value1", {"Stock Code"}, #"SysPro: InvMaster+ (Future PDK)", {"StockCode"}, "SysPro: InvMaster+ (Future PDK)", JoinKind.LeftOuter),
    #"Merged Queries1" = Table.NestedJoin(#"Merged Queries", {"Customer Code"}, #"Salesforce: Account", {"Customer"}, "Salesforce: Account", JoinKind.LeftOuter),
    #"Expanded SysPro: InvMaster+ (Future PDK)" = Table.ExpandTableColumn(#"Merged Queries1", "SysPro: InvMaster+ (Future PDK)", {"ProductUnitType", "ProductFamily", "ProductKeyFeature"}, {"ProductUnitType", "ProductFamily", "ProductKeyFeature"}),
    #"Expanded Salesforce: Account" = Table.ExpandTableColumn(#"Expanded SysPro: InvMaster+ (Future PDK)", "Salesforce: Account", {"Name", "Sub_Key_Account__c"}, {"Name", "Sub_Key_Account__c"}),
    #"Merged Queries2" = Table.NestedJoin(#"Expanded Salesforce: Account", {"Revenue GL Code"}, AccountStructure, {"AccountName.1"}, "AccountStructure", JoinKind.LeftOuter),
    #"Expanded AccountStructure" = Table.ExpandTableColumn(#"Merged Queries2", "AccountStructure", {"Organizational Element", "OE Group"}, {"Organizational Element", "OE Group"}),
    #"Added Custom1" = Table.AddColumn(#"Expanded AccountStructure", "Wholegood Units", each (if [Value] = 0 then 0 else 1) *
(if [ProductUnitType] = "Whole Good" then 1 else 0) *
(if [Organizational Element] = "Ramps" then 0 else 1) *
[Units]),
    #"Changed Type1" = Table.TransformColumnTypes(#"Added Custom1",{{"Wholegood Units", Int64.Type}}),
    #"Removed Columns" = Table.RemoveColumns(#"Changed Type1",{"Units"}),
    #"Removed Other Columns1" = Table.SelectColumns(#"Removed Columns",{"Year-Month", "Sub_Key_Account__c", "Organizational Element", "Wholegood Units"}),
    #"Pivoted Column" = Table.Pivot(#"Removed Other Columns1", List.Distinct(#"Removed Other Columns1"[#"Year-Month"]), "Year-Month", "Wholegood Units", List.Sum)
in
    #"Pivoted Column"