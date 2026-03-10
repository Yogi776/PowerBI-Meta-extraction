let
    Source = Table.FromRows(Json.Document(Binary.Decompress(Binary.FromText("tZPLbsIwEEV/xcqqlVBBIHWPQluQQLHCo0iUhQlTsOo6yI9Q/r4JBBgHwwKJ5ZzcmTuPeDYL2kkCWqeKgyYxZCAtBDVM82iQLrjgZhfMa7MgZCrHijwNPsNnlJKHF1KrMlgiTRcE/zuV57ekwz4pmdvLZeqbgIyZVOH+T8yb8a6Ar9YGu4HKeALkyzYazVcy4DoBIZiE1BYlIrPOJ6YqXdrE6Bq5KS8curuF4s7ke1BdUE9qvgQkOwCPzLC8vuGpfGDTDnmgzyHBOQty83z1HjGyprK8klS3R5kyeJx9fE/f9KNXj2HBjPNUSnJPwZj9bpxSRewddmgUK35Z7b6QI/bnbLlckfaW7ZysM60uaqRs8lOPJ0h9RFXpmCLRmHr9J7SPRHnkVU1bSDRtVY2iUdTn3/iplsRbjHIpWSKANF8a+OIIX1kvbIRrU6CrPtNOiLvuhJeq+T8=", BinaryEncoding.Base64), Compression.Deflate)), let _t = ((type nullable text) meta [Serialized.Text = true]) in type table [#"Product Revenue Group" = _t, #"Organizational Element" = _t, #"OE Group" = _t]),
    #"Changed Type" = Table.TransformColumnTypes(Source,{{"Product Revenue Group", type text}, {"Organizational Element", type text}, {"OE Group", type text}}),
    #"Replaced Value" = Table.ReplaceValue(#"Changed Type","SL Curved Accessories","Helix",Replacer.ReplaceText,{"Organizational Element"}),
    #"Removed Duplicates" = Table.Distinct(#"Replaced Value", {"Product Revenue Group"})
in
    #"Removed Duplicates"