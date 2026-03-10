let
    Source = SharePoint.Files("https://harmar.sharepoint.com/sites/territorytracker", [ApiVersion = 15]),
    Filtered = Table.SelectRows(Source, each [Name] = "Periods-Days.xlsx" and Text.Contains([Folder Path], "/Shared Documents/General/Slim Shady Files/")),
    FileBinary = Filtered{0}[Content],
    Imported = Excel.Workbook(FileBinary),
    Percent_Through_Table = Imported{[Item="Percent_Through",Kind="Table"]}[Data],
    #"Changed Type" = Table.TransformColumnTypes(Percent_Through_Table,{{"Date", type date}, {"Workday", Int64.Type}, {"Year", Int64.Type}, {"Month #", Int64.Type}, {"Month", type text}, {"Day", Int64.Type}, {"Month & Year", type text}, {"WDs Month", Int64.Type}, {"WDs Year", Int64.Type}, {"% Through Month", type number}, {"% Through Year", type number}}),
    #"Added Custom" = Table.AddColumn(#"Changed Type", "PY Date", each Date.AddYears([Date], 1)),
    #"Changed Type1" = Table.TransformColumnTypes(#"Added Custom",{{"PY Date", type date}}),
    #"Added Custom1" = Table.AddColumn(#"Changed Type1", "Yesterday", each Date.AddDays(Date.From(DateTime.LocalNow()), -1)),
    #"Changed Type2" = Table.TransformColumnTypes(#"Added Custom1",{{"Yesterday", type date}}),
    #"Added Conditional Column" = Table.AddColumn(#"Changed Type2", "PY Factor", each if [PY Date] <= [Yesterday] then 1 else 0),
    #"Changed Type3" = Table.TransformColumnTypes(#"Added Conditional Column",{{"PY Factor", Int64.Type}}),
    #"Removed Other Columns" = Table.SelectColumns(#"Changed Type3",{"Workday", "Year", "Month", "Month & Year"}),
    #"Merged Queries" = Table.NestedJoin(#"Removed Other Columns", {"Month"}, Months, {"Month"}, "Months", JoinKind.LeftOuter),
    #"Expanded Months" = Table.ExpandTableColumn(#"Merged Queries", "Months", {"Quarter"}, {"Quarter"}),
    #"Merged Columns" = Table.CombineColumns(Table.TransformColumnTypes(#"Expanded Months", {{"Year", type text}}, "en-US"),{"Year", "Quarter"},Combiner.CombineTextByDelimiter("-", QuoteStyle.None),"Year-Qtr"),
    #"Removed Columns" = Table.RemoveColumns(#"Merged Columns",{"Month", "Month & Year"}),
    #"Reordered Columns" = Table.ReorderColumns(#"Removed Columns",{"Year-Qtr", "Workday"}),
    #"Grouped Rows" = Table.Group(#"Reordered Columns", {"Year-Qtr"}, {{"Working Days", each List.Sum([Workday]), type nullable number}})
in
    #"Grouped Rows"