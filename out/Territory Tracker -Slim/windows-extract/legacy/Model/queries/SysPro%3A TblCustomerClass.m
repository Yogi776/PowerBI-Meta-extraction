let
    Source = Sql.Database("nausawsdb004.harmar.lan", "Harmar"),
    dbo_TblCustomerClass = Source{[Schema="dbo",Item="TblCustomerClass"]}[Data],
    #"Removed Other Columns" = Table.SelectColumns(dbo_TblCustomerClass,{"Description", "Class"}),
    #"Added Custom" = Table.AddColumn(#"Removed Other Columns", "Channel", each if[Class] = "VA" then "VA" else "Non-VA")
in
    #"Added Custom"