let
    Source = Sql.Database("nausawsdb004.harmar.lan", "Harmar"),
    #"dbo_InvMaster+" = Source{[Schema="dbo",Item="InvMaster+"]}[Data],
    #"Removed Other Columns" = Table.SelectColumns(#"dbo_InvMaster+",{"StockCode", "ProductUnitType", "ProductBranch", "ProductCategory", "ProductFamily", "ProductModel", "ProductKeyFeature","ProductLineFin"}),
    #"Filtered Rows" = Table.SelectRows(#"Removed Other Columns", each ([StockCode] <> " ")),
    #"Merged Queries" = Table.NestedJoin(#"Filtered Rows", {"StockCode"}, #"SysPro: InvMaster", {"StockCode"}, "SysPro: InvMaster", JoinKind.LeftOuter),
    #"Expanded SysPro: InvMaster" = Table.ExpandTableColumn(#"Merged Queries", "SysPro: InvMaster", {"Description", "ProductClass"}, {"SysPro: InvMaster.Description", "SysPro: InvMaster.ProductClass"}),
    #"Merged Queries1" = Table.NestedJoin(#"Expanded SysPro: InvMaster", {"SysPro: InvMaster.ProductClass"}, #"SysPro: SalProductClassDes", {"ProductClass"}, "SysPro: SalProductClassDes", JoinKind.LeftOuter),
    #"Expanded SysPro: SalProductClassDes" = Table.ExpandTableColumn(#"Merged Queries1", "SysPro: SalProductClassDes", {"Description"}, {"SysPro: SalProductClassDes.Description"}),
    #"Replaced Value" = Table.ReplaceValue(#"Expanded SysPro: SalProductClassDes",null,"No PDK",Replacer.ReplaceValue,{"ProductUnitType", "ProductBranch", "ProductCategory", "ProductLineFin", "ProductFamily", "ProductModel", "ProductKeyFeature"}),
    #"Filtered Rows1" = Table.SelectRows(#"Replaced Value", each ([StockCode] <> "RPL400") and ([ProductUnitType] <> "Retired" and [ProductUnitType] <> "REV A" and [ProductUnitType] <> "Rev A")),
    #"Renamed Columns" = Table.RenameColumns(#"Filtered Rows1",{{"SysPro: InvMaster.Description", "Description"}, {"SysPro: InvMaster.ProductClass", "ProductClass"}, {"SysPro: SalProductClassDes.Description", "ProductClassDescription"}}),
    #"Appended Query" = Table.Combine({#"Renamed Columns", PDK_Forecast})
in
    #"Appended Query"