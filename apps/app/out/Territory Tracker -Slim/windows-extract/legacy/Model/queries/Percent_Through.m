let
    Site = "https://harmar.sharepoint.com/sites/territorytracker",
    Source = SharePoint.Files(Site, [ApiVersion = 15]),
    FileRows = Table.SelectRows(Source, each [Name] = "Periods-Days.xlsx"),
    FileContent = if Table.RowCount(FileRows) > 0 then FileRows{0}[Content] else error "File not found: Periods-Days.xlsx",
    WB = Excel.Workbook(FileContent, true),
    PT_Candidate = Table.SelectRows(WB, each Text.Upper([Name]) = "PERCENT_THROUGH" and [Kind] = "Table"),
    Percent_Through_Table = if Table.RowCount(PT_Candidate) > 0 then PT_Candidate{0}[Data] else error "Missing query: Percent_Through",
    NormalizedCols = Table.TransformColumnNames(Percent_Through_Table, each Text.Trim(Text.Replace(_, "#(tab)", " "))),
    ChangedType = Table.TransformColumnTypes(NormalizedCols, {
        {"Date", type date},
        {"Workday", Int64.Type},
        {"Year", Int64.Type},
        {"Month #", Int64.Type},
        {"Month", type text},
        {"Day", Int64.Type},
        {"Month & Year", type text},
        {"WDs Month", Int64.Type},
        {"WDs Year", Int64.Type},
        {"% Through Month", type number},
        {"% Through Year", type number}
    }),
    AddedPY = Table.AddColumn(ChangedType, "PY Date", each Date.AddYears([Date], 1), type date),
    AddedYesterday = Table.AddColumn(AddedPY, "Yesterday", each Date.AddDays(Date.From(DateTime.LocalNow()), -1), type date),
    AddedPYFactor = Table.AddColumn(AddedYesterday, "PY Factor", each if [PY Date] <= [Yesterday] then 1 else 0, Int64.Type)
in
    AddedPYFactor