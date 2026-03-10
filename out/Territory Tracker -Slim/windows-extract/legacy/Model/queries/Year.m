let
    Source = Table.FromRows(Json.Document(Binary.Decompress(Binary.FromText("Ncy5DcAgEADBXogJ4JbHrgXRfxtGFptNNGulKFHSzj+qCIFoooshpnjEe4EzzjjjjDPOOOOMM87tzPsD", BinaryEncoding.Base64), Compression.Deflate)), let _t = ((type nullable text) meta [Serialized.Text = true]) in type table [Year = _t]),
    #"Changed Type" = Table.TransformColumnTypes(Source,{{"Year", Int64.Type}}),
    #"Added Custom" = Table.AddColumn(#"Changed Type", "Current Year", each if [Year] = Date.Year(DateTime.LocalNow())
 then "Current Year" else if[Year]= Date.Year(DateTime.LocalNow())
-1 then "Prior Year" else ""),
    #"Changed Type1" = Table.TransformColumnTypes(#"Added Custom",{{"Current Year", type text}})
in
    #"Changed Type1"