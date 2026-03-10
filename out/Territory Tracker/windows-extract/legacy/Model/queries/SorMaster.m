let
    Source = Sql.Database("nausawsdb004.harmar.lan", "Harmar"),
    dbo_SorMaster = Source{[Schema="dbo",Item="SorMaster"]}[Data]
in
    dbo_SorMaster