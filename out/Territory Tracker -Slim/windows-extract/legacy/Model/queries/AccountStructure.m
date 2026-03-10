let
    Source = Sql.Database("nausawsdb004", "LucanetPowerBI"),
    dbo_AccountStructure = Source{[Schema="dbo",Item="AccountStructure"]}[Data],
    #"Filtered Rows" = Table.SelectRows(dbo_AccountStructure, each ([WorkspaceID] = "PL")),
    #"Filtered Rows1" = Table.SelectRows(#"Filtered Rows", each Text.StartsWith([AccountName], "4")),
    #"Filtered Rows3" = Table.SelectRows(#"Filtered Rows1", each true),
    #"Filtered Rows2" = Table.SelectRows(#"Filtered Rows3", each [AccountLevel3] <> "Pollock Revenue" and [AccountLevel3] <> "Miscellaneous"),
    #"Split Column by Delimiter" = Table.SplitColumn(#"Filtered Rows2", "AccountName", Splitter.SplitTextByEachDelimiter({" "}, QuoteStyle.Csv, false), {"AccountName.1", "AccountName.2"}),
    #"Changed Type" = Table.TransformColumnTypes(#"Split Column by Delimiter",{{"AccountName.1", type text}, {"AccountName.2", type text}}),
    #"Removed Other Columns" = Table.SelectColumns(#"Changed Type",{"AccountName.1", "AccountLevel3", "AccountLevel4", "AccountLevel5"}),
    #"Replaced Value" = Table.ReplaceValue(#"Removed Other Columns"," (OID: 2408148)","",Replacer.ReplaceText,{"AccountLevel4"}),
    #"Added Conditional Column" = Table.AddColumn(#"Replaced Value", "Account Level4-5", each if [AccountLevel5] = "Elevators Revenue" then [AccountLevel5] else [AccountLevel4]),
    #"Changed Type1" = Table.TransformColumnTypes(#"Added Conditional Column",{{"Account Level4-5", type text}}),
    #"Renamed Columns" = Table.RenameColumns(#"Changed Type1",{{"Account Level4-5", "Product Revenue Group"}}),
    #"Merged Queries" = Table.NestedJoin(#"Renamed Columns", {"Product Revenue Group"}, #"Organizational Elements", {"Product Revenue Group"}, "Table", JoinKind.LeftOuter),
    #"Expanded Table" = Table.ExpandTableColumn(#"Merged Queries", "Table", {"Organizational Element", "OE Group"}, {"Organizational Element", "OE Group"})
in
    #"Expanded Table"