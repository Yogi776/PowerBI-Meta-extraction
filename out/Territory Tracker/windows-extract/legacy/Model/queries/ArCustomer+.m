let
    Source = Sql.Database("nausawsdb004.harmar.lan", "Harmar"),
    #"dbo_ArCustomer+" = Source{[Schema="dbo",Item="ArCustomer+"]}[Data]
in
    #"dbo_ArCustomer+"