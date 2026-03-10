let
    Source = Sql.Database("nausawsdb004.harmar.lan", "Harmar"),
    dbo_ArCustomer = Source{[Schema="dbo",Item="ArCustomer"]}[Data],
    #"Renamed Columns" = Table.RenameColumns(dbo_ArCustomer,{{"Salesperson", "Territory"}, {"CustomerClass", "Channel"}}),
    #"Replaced Value" = Table.ReplaceValue(#"Renamed Columns","","A",Replacer.ReplaceValue,{"BuyingGroup1"}),
    #"Merged Queries" = Table.NestedJoin(#"Replaced Value", {"BuyingGroup1"}, Harmar_Pricebooks, {"CustomerBuyGrp"}, "Harmar_Pricebooks", JoinKind.LeftOuter),
    #"Expanded Harmar_Pricebooks" = Table.ExpandTableColumn(#"Merged Queries", "Harmar_Pricebooks", {"Contract"}, {"Harmar_Pricebooks.Contract"}),
    #"Extracted First Characters" = Table.TransformColumns(#"Expanded Harmar_Pricebooks", {{"SoldPostalCode", each Text.Start(_, 5), type text}}),
    #"Extracted First Characters1" = Table.TransformColumns(#"Extracted First Characters", {{"ShipPostalCode", each Text.Start(_, 5), type text}})
in
    #"Extracted First Characters1"