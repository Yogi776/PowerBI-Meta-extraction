let
    Source = Sql.Database("nausawsdb004.harmar.lan", "Harmar"),
    dbo_SalProductClass = Source{[Schema="dbo",Item="SalProductClass"]}[Data],
    #"Removed Duplicates" = Table.Distinct(dbo_SalProductClass, {"ProductClass"}),
    #"Removed Blank Rows" = Table.SelectRows(#"Removed Duplicates", each not List.IsEmpty(List.RemoveMatchingItems(Record.FieldValues(_), {"", null}))),
    #"Removed Errors" = Table.RemoveRowsWithErrors(#"Removed Blank Rows", {"ProductClass"}),
    #"Removed Other Columns" = Table.SelectColumns(#"Removed Errors",{"ProductClass", "Description"}),
    #"Uppercased Text" = Table.TransformColumns(#"Removed Other Columns",{{"Description", Text.Upper, type text}}),
    #"Replaced Value" = Table.ReplaceValue(#"Uppercased Text","MISC  CHARGES","MISC CHARGES",Replacer.ReplaceText,{"Description"})
in
    #"Replaced Value"