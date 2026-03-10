let
    Source = SharePoint.Files("https://harmar.sharepoint.com/sites/territorytracker", [ApiVersion = 15]),
    #"Filtered Rows" = Table.SelectRows(Source, each ([Name] = "PDK - KP Edit 9.10.25.xlsx")),
    #"PDK - KP Edit 9 10 25 xlsx_https://harmar sharepoint com/sites/territorytracker/Shared Documents/General/Slim Shady Files/" = #"Filtered Rows"{[Name="PDK - KP Edit 9.10.25.xlsx",#"Folder Path"="https://harmar.sharepoint.com/sites/territorytracker/Shared Documents/General/Slim Shady Files/"]}[Content],
    #"Imported Excel Workbook" = Excel.Workbook(#"PDK - KP Edit 9 10 25 xlsx_https://harmar sharepoint com/sites/territorytracker/Shared Documents/General/Slim Shady Files/"),
    PDK_Forecast_Table = #"Imported Excel Workbook"{[Item="PDK_Forecast",Kind="Table"]}[Data],
    #"Changed Type" = Table.TransformColumnTypes(PDK_Forecast_Table,{{"StockCode", type text}, {"ProductUnitType", type text}, {"ProductFamily", type text}, {"ProductKeyFeature", type text}, {"ProductBranch", type text}, {"ProductCategory", type text}, {"ProductModel", type text}, {"ProductLineFin", type text}, {"Description", type text}, {"ProductClass", type text}, {"ProductClassDescription", type text}})
in
    #"Changed Type"