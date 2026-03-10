let
    Source = Sql.Database("nausawsdb004.harmar.lan", "Harmar"),
    dbo_InvMaster = Source{[Schema="dbo",Item="InvMaster"]}[Data]
in
    dbo_InvMaster