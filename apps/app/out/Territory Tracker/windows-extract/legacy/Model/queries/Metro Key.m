let
    Source = SharePoint.Files("https://harmar.sharepoint.com/sites/territorytracker/", [ApiVersion = 15]),
    #"Filtered Rows" = Table.SelectRows(Source, each ([Extension] <> ".pbix")),
    #"Metro Map Key xlsx_https://harmar sharepoint com/sites/territorytracker/Shared Documents/General/" = #"Filtered Rows"{[Name="Metro Map Key.xlsx",#"Folder Path"="https://harmar.sharepoint.com/sites/territorytracker/Shared Documents/General/"]}[Content],
    #"Imported Excel Workbook" = Excel.Workbook(#"Metro Map Key xlsx_https://harmar sharepoint com/sites/territorytracker/Shared Documents/General/"),
    Sheet1_Sheet = #"Imported Excel Workbook"{[Item="Sheet1",Kind="Sheet"]}[Data],
    #"Promoted Headers" = Table.PromoteHeaders(Sheet1_Sheet, [PromoteAllScalars=true]),
    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers",{{"Unique ID", type text}, {"ZipCode", Int64.Type}, {"City", type text}, {"State", type text}, {"State Name", type text}, {"County", type text}, {"MSA", type text}}),
    #"Replaced Value" = Table.ReplaceValue(#"Changed Type","","Non-Metro",Replacer.ReplaceValue,{"MSA"})
in
    #"Replaced Value"