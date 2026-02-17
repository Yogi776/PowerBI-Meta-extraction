let
    Source = Sql.Database("nausawsdb004.harmar.lan", "Harmar"),
    dbo_GenTransaction = Source{[Schema="dbo",Item="GenTransaction"]}[Data],
    #"Filtered Rows1" = Table.SelectRows(dbo_GenTransaction, each Text.StartsWith([GlCode], "4")),
    #"Filtered Rows" = Table.SelectRows(#"Filtered Rows1", each ([GlYear] = 2025 or [GlYear] = 2023 or [GlYear] = 2024)),
    #"Changed Type" = Table.TransformColumnTypes(#"Filtered Rows",{{"JnlDate", type datetime}}),
    #"Appended Query" = Table.Combine({#"Changed Type", #"PRES 2024 Revenue"})
in
    #"Appended Query"