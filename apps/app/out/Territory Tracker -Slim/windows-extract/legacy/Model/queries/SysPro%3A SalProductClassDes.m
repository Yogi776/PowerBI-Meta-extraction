let
    Source = Sql.Database("nausawsdb004.harmar.lan", "Harmar"),
    dbo_SalProductClassDes = Source{[Schema="dbo",Item="SalProductClassDes"]}[Data],
    #"Capitalized Each Word" = Table.TransformColumns(dbo_SalProductClassDes,{{"Description", Text.Proper, type text}}),
    #"Replaced Value" = Table.ReplaceValue(#"Capitalized Each Word","Up","UP",Replacer.ReplaceText,{"Description"}),
    #"Replaced Value1" = Table.ReplaceValue(#"Replaced Value","Vpl","VPL",Replacer.ReplaceText,{"Description"}),
    #"Replaced Value2" = Table.ReplaceValue(#"Replaced Value1","Mwc","MWC",Replacer.ReplaceText,{"Description"}),
    #"Replaced Value3" = Table.ReplaceValue(#"Replaced Value2","Sl","SL",Replacer.ReplaceText,{"Description"})
in
    #"Replaced Value3"