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
    #"Removed Other Columns" = Table.SelectColumns(#"Added Custom",{"GlCode", "JnlDate", "EntryValue", "SubModArInvoice", "SubModCustomer", "SubModStock", "Year-Month"}),
    #"Reordered Columns2" = Table.ReorderColumns(#"Removed Other Columns",{"JnlDate", "GlCode", "EntryValue", "SubModArInvoice", "SubModCustomer", "SubModStock", "Year-Month"}),
    #"Changed Type8" = Table.TransformColumnTypes(#"Reordered Columns2",{{"JnlDate", type date}}),
    #"Reordered Columns" = Table.ReorderColumns(#"Changed Type8",{"Year-Month", "GlCode", "SubModArInvoice", "SubModCustomer", "SubModStock", "EntryValue"}),
    #"Changed Type9" = Table.TransformColumnTypes(#"Reordered Columns",{{"JnlDate", type text}}),
    #"Merged Columns" = Table.CombineColumns(#"Changed Type9",{"Year-Month", "GlCode", "SubModArInvoice", "SubModCustomer", "SubModStock"},Combiner.CombineTextByDelimiter("|", QuoteStyle.None),"Merged"),
    #"Removed Columns" = Table.RemoveColumns(#"Merged Columns",{"EntryValue"}),
    #"Removed Duplicates" = Table.Distinct(#"Removed Columns", {"Merged"})
in
    #"Removed Duplicates"