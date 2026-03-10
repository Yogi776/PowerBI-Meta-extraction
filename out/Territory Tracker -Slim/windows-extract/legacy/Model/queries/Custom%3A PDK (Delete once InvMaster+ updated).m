let
    Source = SharePoint.Files("https://harmar.sharepoint.com/sites/territorytracker", [ApiVersion = 15]),
    #"Sorted Rows" = Table.Sort(Source,{{"Date modified", Order.Descending}}),
    #"Product Dimension Key xlsx_https://harmar sharepoint com/sites/territorytracker/Shared Documents/General/" = #"Sorted Rows"{[Name="Product Dimension Key.xlsx",#"Folder Path"="https://harmar.sharepoint.com/sites/territorytracker/Shared Documents/General/"]}[Content],
    #"Imported Excel Workbook" = Excel.Workbook(#"Product Dimension Key xlsx_https://harmar sharepoint com/sites/territorytracker/Shared Documents/General/"),
    #"4  Set Stock Code Dimensions_Sheet" = #"Imported Excel Workbook"{[Item="4. Set Stock Code Dimensions",Kind="Sheet"]}[Data],
    #"Removed Errors" = Table.RemoveRowsWithErrors(#"4  Set Stock Code Dimensions_Sheet", {"Column2"}),
    #"Promoted Headers" = Table.PromoteHeaders(#"Removed Errors", [PromoteAllScalars=true]),
    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers",{{"StockCode", type text}, {"Description", type text}, {"ProductClass", type text}, {"Product Class Description", type text}, {"Unit Type", type text}, {"Product Branch", type text}, {"Product Category", type text}, {"Product Line", type text}, {"Family", type text}, {"Model", type text}, {"Key Feature", type text}})
in
    #"Changed Type"