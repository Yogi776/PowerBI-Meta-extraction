let
    Source = Sql.Database("nausawsdb004.harmar.lan", "Harmar"),
    dbo_ArTrnDetail = Source{[Schema="dbo",Item="ArTrnDetail"]}[Data],
    #"Filtered Rows" = Table.SelectRows(dbo_ArTrnDetail, each [TrnYear] > 2019),
    #"Duplicated Column" = Table.DuplicateColumn(#"Filtered Rows", "Customer", "Customer - Copy"),
    #"Extracted Last Characters" = Table.TransformColumns(#"Duplicated Column", {{"Customer - Copy", each Text.End(_, 7), type text}}),
    #"Renamed Columns" = Table.RenameColumns(#"Extracted Last Characters",{{"Customer - Copy", "Salesforce Connector"}}),
    #"Filtered Rows1" = Table.SelectRows(#"Renamed Columns", each Text.StartsWith([TransactionGlCode], "4")),
    #"Added Custom" = Table.AddColumn(#"Filtered Rows1", "Year-Month", each Text.From([TrnYear]) & "-" & Text.PadStart(Text.From([TrnMonth]), 2, "0")),
    #"Removed Other Columns" = Table.SelectColumns(#"Added Custom",{"Invoice", "InvoiceDate", "Customer", "StockCode", "QtyInvoiced", "TransactionGlCode", "Year-Month"}),
    #"Changed Type1" = Table.TransformColumnTypes(#"Removed Other Columns",{{"InvoiceDate", type date}}),
    #"Reordered Columns2" = Table.ReorderColumns(#"Changed Type1",{"InvoiceDate", "Invoice", "Customer", "StockCode", "QtyInvoiced", "TransactionGlCode", "Year-Month"}),
    #"Reordered Columns" = Table.ReorderColumns(#"Reordered Columns2",{"Year-Month", "TransactionGlCode", "Invoice", "Customer", "StockCode", "QtyInvoiced"}),
    #"Changed Type2" = Table.TransformColumnTypes(#"Reordered Columns",{{"InvoiceDate", type text}}),
    #"Removed Other Columns1" = Table.SelectColumns(#"Changed Type2",{"InvoiceDate", "Invoice"}),
    #"Changed Type" = Table.TransformColumnTypes(#"Removed Other Columns1",{{"InvoiceDate", type date}}),
    #"Removed Duplicates" = Table.Distinct(#"Changed Type", {"Invoice"})
in
    #"Removed Duplicates"