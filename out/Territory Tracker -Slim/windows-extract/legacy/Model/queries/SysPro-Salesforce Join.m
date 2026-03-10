let
    Source = Sql.Database("nausawsdb004.harmar.lan", "Harmar"),
    dbo_ArTrnDetail = Source{[Schema="dbo",Item="ArTrnDetail"]}[Data],
    #"Filtered Rows" = Table.SelectRows(dbo_ArTrnDetail, each [TrnYear] > 2019),
    #"Duplicated Column" = Table.DuplicateColumn(#"Filtered Rows", "Customer", "Customer - Copy"),
    #"Extracted Last Characters" = Table.TransformColumns(#"Duplicated Column", {{"Customer - Copy", each Text.End(_, 7), type text}}),
    #"Renamed Columns" = Table.RenameColumns(#"Extracted Last Characters",{{"Customer - Copy", "Salesforce Connector"}}),
    #"Filtered Rows1" = Table.SelectRows(#"Renamed Columns", each Text.StartsWith([TransactionGlCode], "4")),
    #"Added Custom" = Table.AddColumn(#"Filtered Rows1", "Year-Month", each Text.From([TrnYear]) & "-" & Text.PadStart(Text.From([TrnMonth]), 2, "0")),
    #"Removed Other Columns" = Table.SelectColumns(#"Added Custom",{"Customer", "CustomerClass", "Salesforce Connector"}),
    #"Removed Duplicates1" = Table.Distinct(#"Removed Other Columns", {"Customer"}),
    #"Merged Columns" = Table.CombineColumns(#"Removed Duplicates1",{"Customer", "Salesforce Connector"},Combiner.CombineTextByDelimiter("|", QuoteStyle.None),"Merged"),
    #"Removed Duplicates" = Table.Distinct(#"Merged Columns"),
    #"Split Column by Delimiter" = Table.SplitColumn(#"Removed Duplicates", "Merged", Splitter.SplitTextByDelimiter("|", QuoteStyle.Csv), {"Merged.1", "Merged.2"}),
    #"Renamed Columns1" = Table.RenameColumns(#"Split Column by Delimiter",{{"Merged.1", "Customer"}, {"Merged.2", "Salesforce Connector"}}),
    #"Reordered Columns" = Table.ReorderColumns(#"Renamed Columns1",{"Customer", "Salesforce Connector", "CustomerClass"}),
    #"Merged Queries" = Table.NestedJoin(#"Reordered Columns", {"CustomerClass"}, #"SysPro: TblCustomerClass", {"Class"}, "SysPro: TblCustomerClass", JoinKind.LeftOuter),
    #"Expanded SysPro: TblCustomerClass" = Table.ExpandTableColumn(#"Merged Queries", "SysPro: TblCustomerClass", {"Channel"}, {"Channel"})
in
    #"Expanded SysPro: TblCustomerClass"