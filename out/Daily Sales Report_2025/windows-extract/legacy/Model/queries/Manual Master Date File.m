let
    Source = SharePoint.Files("https://harmar.sharepoint.com/sites/territorytracker", [ApiVersion = 15]),
    #"Filtered Rows" = Table.SelectRows(Source, each ([Name] = "Days-Months.xlsx")),
    #"Days-Months xlsx_https://harmar sharepoint com/sites/territorytracker/Shared Documents/General/" = #"Filtered Rows"{[Name="Days-Months.xlsx",#"Folder Path"="https://harmar.sharepoint.com/sites/territorytracker/Shared Documents/General/"]}[Content],
    #"Imported Excel Workbook" = Excel.Workbook(#"Days-Months xlsx_https://harmar sharepoint com/sites/territorytracker/Shared Documents/General/"),
    #"Filtered Rows1" = Table.SelectRows(#"Imported Excel Workbook", each ([Name] = "Dates_Master")),
    #"Expanded Data" = Table.ExpandTableColumn(#"Filtered Rows1", "Data", {"Date", "End of Month", "Weekday #", "Weekday", "Weekend", "Holiday", "Non Workday", "Year", "Month #", "Month", "Day", "Month & Year", "Paycheck Date?"}, {"Data.Date", "Data.End of Month", "Data.Weekday #", "Data.Weekday", "Data.Weekend", "Data.Holiday", "Data.Non Workday", "Data.Year", "Data.Month #", "Data.Month", "Data.Day", "Data.Month & Year", "Data.Paycheck Date?"}),
    #"Removed Columns" = Table.RemoveColumns(#"Expanded Data",{"Item", "Kind", "Hidden"}),
    #"Replaced Value" = Table.ReplaceValue(#"Removed Columns",0,2,Replacer.ReplaceValue,{"Data.Non Workday"}),
    #"Replaced Value1" = Table.ReplaceValue(#"Replaced Value",1,0,Replacer.ReplaceValue,{"Data.Non Workday"}),
    #"Replaced Value2" = Table.ReplaceValue(#"Replaced Value1",2,1,Replacer.ReplaceValue,{"Data.Non Workday"})
in
    #"Replaced Value2"