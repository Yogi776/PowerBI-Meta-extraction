let
    Source = Sql.Database("nausawsdb004.harmar.lan", "Harmar"),
    dbo_ArTrnDetail = Source{[Schema="dbo",Item="ArTrnDetail"]}[Data],
    #"Filtered Rows" = Table.SelectRows(dbo_ArTrnDetail, each ([TrnYear] = 2025 or [TrnYear] = 2023 or [TrnYear] = 2024)),
    #"Replaced Value" = Table.ReplaceValue(#"Filtered Rows","M","SRQ",Replacer.ReplaceText,{"Branch"}),
    #"Replaced Value1" = Table.ReplaceValue(#"Replaced Value","A","RM",Replacer.ReplaceText,{"Branch"}),
    #"Filtered Rows1" = Table.SelectRows(#"Replaced Value1", each Text.StartsWith([TransactionGlCode], "4") or [TransactionGlCode] = ""),
    #"Appended Query" = Table.Combine({#"Filtered Rows1", #"PRES 2024 Units"})
in
    #"Appended Query"