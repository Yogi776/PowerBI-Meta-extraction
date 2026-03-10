let
    Source = Sql.Database("nausawsdb004.harmar.lan", "Harmar"),
    dbo_Harmar_Pricebooks = Source{[Schema="dbo",Item="Harmar_Pricebooks"]}[Data]
in
    dbo_Harmar_Pricebooks