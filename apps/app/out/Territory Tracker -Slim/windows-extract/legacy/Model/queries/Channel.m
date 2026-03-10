let
    Source = SharePoint.Files("https://harmar.sharepoint.com/sites/territorytracker", [ApiVersion = 15]),
    #"Filtered Rows" = Table.SelectRows(Source, each ([Name] = "2026 Forecast.xlsx")),
    #"2026 Forecast xlsx_https://harmar sharepoint com/sites/territorytracker/Shared Documents/General/Slim Shady Files/" = #"Filtered Rows"{[Name="2026 Forecast.xlsx",#"Folder Path"="https://harmar.sharepoint.com/sites/territorytracker/Shared Documents/General/Slim Shady Files/"]}[Content],
    #"Imported Excel Workbook" = Excel.Workbook(#"2026 Forecast xlsx_https://harmar sharepoint com/sites/territorytracker/Shared Documents/General/Slim Shady Files/"),
    Channel_Table = #"Imported Excel Workbook"{[Item="Channel",Kind="Table"]}[Data],
    #"Changed Type" = Table.TransformColumnTypes(Channel_Table,{{"Standard Account Revenue 2025-01 to 2025-08", type text}, {"Non-VA", Int64.Type}, {"VA", Int64.Type}, {"Total", Int64.Type}, {"VA %", type number}})
in
    #"Changed Type"