let
    Source = Sql.Database("nausawsdb004.harmar.lan", "Harmar"),
    #"dbo_InvMaster+" = Source{[Schema="dbo",Item="InvMaster+"]}[Data],
    #"Removed Other Columns" = Table.SelectColumns(#"dbo_InvMaster+",{"StockCode", "ProductUnitType"}),
    #"Removed Errors" = Table.RemoveRowsWithErrors(#"Removed Other Columns", {"StockCode"})
in
    #"Removed Errors"