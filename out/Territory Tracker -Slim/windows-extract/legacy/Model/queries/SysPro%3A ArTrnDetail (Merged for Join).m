let
    Source = Sql.Database("nausawsdb004.harmar.lan", "Harmar"),
    dbo_ArTrnDetail = Source{[Schema="dbo",Item="ArTrnDetail"]}[Data],
    #"Filtered Rows" = Table.SelectRows(dbo_ArTrnDetail, each [TrnYear] > 2019),
    #"Duplicated Column" = Table.DuplicateColumn(#"Filtered Rows", "Customer", "Customer - Copy"),
    #"Extracted Last Characters" = Table.TransformColumns(#"Duplicated Column", {{"Customer - Copy", each Text.End(_, 7), type text}}),
    #"Renamed Columns" = Table.RenameColumns(#"Extracted Last Characters",{{"Customer - Copy", "Salesforce Connector"}}),
    #"Filtered Rows1" = Table.SelectRows(#"Renamed Columns", each Text.StartsWith([TransactionGlCode], "4")),
    #"Added Custom" = Table.AddColumn(#"Filtered Rows1", "Year-Month", each Text.From([TrnYear]) & "-" & Text.PadStart(Text.From([TrnMonth]), 2, "0")),
    #"Removed Other Columns" = Table.SelectColumns(#"Added Custom",{"Invoice", "Customer", "StockCode", "QtyInvoiced", "TransactionGlCode", "Year-Month"}),
    #"Reordered Columns2" = Table.ReorderColumns(#"Removed Other Columns",{"Invoice", "Customer", "StockCode", "QtyInvoiced", "TransactionGlCode", "Year-Month"}),
    #"Reordered Columns" = Table.ReorderColumns(#"Reordered Columns2",{"Year-Month", "TransactionGlCode", "Invoice", "Customer", "StockCode", "QtyInvoiced"}),
    #"Merged Columns" = Table.CombineColumns(#"Reordered Columns",{"Year-Month", "TransactionGlCode", "Invoice", "Customer", "StockCode"},Combiner.CombineTextByDelimiter("|", QuoteStyle.None),"Merged"),
    #"Grouped Rows" = Table.Group(#"Merged Columns", {"Merged"}, {{"Units", each List.Sum([QtyInvoiced]), type number}}),
    #"Reordered Columns1" = Table.ReorderColumns(#"Grouped Rows",{"Merged", "Units"}),
    #"Changed Type" = Table.TransformColumnTypes(#"Reordered Columns1",{{"Units", Int64.Type}})
in
    #"Changed Type"