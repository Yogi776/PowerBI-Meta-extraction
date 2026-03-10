let
    Source = SharePoint.Files("https://harmar.sharepoint.com/sites/territorytracker", [ApiVersion = 15]),
    #"Filtered Rows" = Table.SelectRows(Source, each ([Name] = "2026 Forecast.xlsx")),
    #"2026 Forecast xlsx_https://harmar sharepoint com/sites/territorytracker/Shared Documents/General/Slim Shady Files/" = #"Filtered Rows"{[Name="2026 Forecast.xlsx",#"Folder Path"="https://harmar.sharepoint.com/sites/territorytracker/Shared Documents/General/Slim Shady Files/"]}[Content],
    #"Imported Excel Workbook" = Excel.Workbook(#"2026 Forecast xlsx_https://harmar sharepoint com/sites/territorytracker/Shared Documents/General/Slim Shady Files/"),
    Units_Table = #"Imported Excel Workbook"{[Item="Units",Kind="Table"]}[Data],
    #"Removed Columns" = Table.RemoveColumns(Units_Table,{"Key Account & OE",  "Proportion"}),
    #"Changed Type" = Table.TransformColumnTypes(#"Removed Columns",{{"Territory", type text}, {"2025-09", Int64.Type}, {"2025-10", Int64.Type}, {"2025-11", Int64.Type}, {"2025-12", Int64.Type}, {"2026-01", Int64.Type}, {"2026-02", Int64.Type}, {"2026-03", Int64.Type}, {"2026-04", Int64.Type}, {"2026-05", Int64.Type}, {"2026-06", Int64.Type}, {"2026-07", Int64.Type}, {"2026-08", Int64.Type}, {"2026-09", Int64.Type}, {"2026-10", Int64.Type}, {"2026-11", Int64.Type}, {"2026-12", Int64.Type}, {"Key Account & Territory", type text}, {"Sub_Key_Account__c", type text}, {"Organizational Element", type text}, {"Revenue GL Code", type text}, {"ProductUnitType", type text}}),
    #"Renamed Columns" = Table.RenameColumns(#"Changed Type",{{"Key Account & Territory", "Name"}}),
    #"Unpivoted Columns" = Table.UnpivotOtherColumns(#"Renamed Columns", {"Name", "Sub_Key_Account__c", "Organizational Element", "Revenue GL Code", "ProductUnitType", "Territory"}, "Attribute", "Value"),
    #"Renamed Columns1" = Table.RenameColumns(#"Unpivoted Columns",{{"Attribute", "Year-Month"}, {"Value", "Wholegood Units"}})
in
    #"Renamed Columns1"