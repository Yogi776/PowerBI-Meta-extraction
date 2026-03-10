let
    Source = Sql.Database("nausawsdb004.harmar.lan", "Harmar"),
    dbo_GenTransaction = Source{[Schema="dbo",Item="GenTransaction"]}[Data],
    #"Filtered Rows" = Table.SelectRows(dbo_GenTransaction, each [GlYear] > 2022),
    #"Filtered Rows1" = Table.SelectRows(#"Filtered Rows", each Text.StartsWith([GlCode], "4")),
    #"Added Custom" = Table.AddColumn(#"Filtered Rows1", "Visual_Day", each Date.Day([JnlDate])),
    #"Added Custom1" = Table.AddColumn(#"Added Custom", "Visual_Amount", each -[EntryValue]),
    #"Changed Type" = Table.TransformColumnTypes(#"Added Custom1",{{"Visual_Day", Int64.Type}, {"Visual_Amount", type number}}),
    #"Added Custom2" = Table.AddColumn(#"Changed Type", "Lookup_GL Mapping", each Text.Start([GlCode],5)),
    #"Merged Queries" = Table.NestedJoin(#"Added Custom2", {"SubModStock"}, InvMaster, {"StockCode"}, "InvMaster", JoinKind.LeftOuter),
    #"Expanded InvMaster" = Table.ExpandTableColumn(#"Merged Queries", "InvMaster", {"ProductClass"}, {"InvMaster.ProductClass"}),
    #"Renamed Columns" = Table.RenameColumns(#"Expanded InvMaster",{{"InvMaster.ProductClass", "Calc InvMaster.ProductClass"}})
in
    #"Renamed Columns"